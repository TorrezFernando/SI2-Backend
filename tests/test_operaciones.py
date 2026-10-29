import unittest
from decimal import Decimal
from datetime import date
from unittest.mock import patch
import _fixtures as fixtures
import operaciones as op
from database.models import Usuario, Contrato
from fastapi import HTTPException

class OperacionesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls): fixtures.Regression.setUpClass.__func__(cls)
    def setUp(self):
        fixtures.Regression.setUp(self)
        self.db=fixtures.database.SessionLocal()
        self.admin=self.db.get(Usuario,1);self.client=self.db.get(Usuario,3);self.other=self.db.get(Usuario,4)
        data=op.AltaContrato(id_cliente=1,id_propiedad=1,id_agente=1,tipo_contrato='Alquiler',monto_total='100.00',fecha_inicio=date(2026,1,1),cuotas=3,primer_vencimiento=date(2026,1,31))
        self.cid=op.alta_contrato(data,self.db,self.admin)['id_contrato']
    def tearDown(self): self.db.close()
    def test_schedule_and_own_account(self):
        account=op.mi_cuenta(self.db,self.client)['contratos'][0]
        self.assertEqual(sum(q['monto'] for q in account['cuotas']),Decimal('100'))
        self.assertEqual(account['cuotas'][1]['vencimiento'],date(2026,2,28))
        self.assertEqual(op.mi_cuenta(self.db,self.other)['contratos'],[])
        with self.assertRaises(HTTPException):op.cuotas(self.cid,self.db,self.other)
    def test_payment_idempotency_pdf_and_overpayment(self):
        q=op.cuotas(self.cid,self.db,self.client)[0]
        data=op.PagoCuota(monto='10',clave_idempotencia='prueba-123',confirma_simulacion=True)
        p=op.pagar(q['id'],data,self.db,self.admin)
        self.assertTrue(op.pagar(q['id'],data,self.db,self.admin)['duplicado'])
        self.assertTrue(op.recibo(self.db,self.client,p['id_pago'])[1].startswith(b'%PDF'))
        with self.assertRaises(HTTPException):op.recibo(self.db,self.other,p['id_pago'])
        with self.assertRaises(HTTPException):op.pagar(q['id'],op.PagoCuota(monto='99',clave_idempotencia='prueba-456',confirma_simulacion=True),self.db,self.admin)
        with patch.dict('os.environ',{'SMTP_HOST':''}):
            with self.assertRaises(HTTPException) as e:op.enviar_recibo(p['id_pago'],self.db,self.client)
            self.assertEqual(e.exception.status_code,503)
    def test_token_rotation_and_ownership(self):
        data=op.TokenFCM(dispositivo='telefono',token='a'*40,plataforma='android')
        row=op.registrar_token(data,self.db,self.client)
        updated=op.registrar_token(data.model_copy(update={'token':'b'*40}),self.db,self.client)
        self.assertEqual(row['id'],updated['id'])
        with self.assertRaises(HTTPException):op.baja_token(row['id'],self.db,self.other)
        op.baja_token(row['id'],self.db,self.client)
        self.assertEqual(op.tokens(self.db,self.client),[])
    def test_valuation_permissions_and_comparables(self):
        with self.assertRaises(HTTPException) as e:op.tasar(op.TasacionRequest(id_propiedad=1),self.db,self.client)
        self.assertEqual(e.exception.status_code,403)
        self.admin.tenant.plan='premium';self.db.flush()
        with self.assertRaises(HTTPException) as e:op.tasar(op.TasacionRequest(id_propiedad=1),self.db,self.admin)
        self.assertEqual(e.exception.status_code,422)
    def test_tiny_schedule_never_negative(self):
        data=op.AltaContrato(id_cliente=1,id_propiedad=1,id_agente=1,tipo_contrato='Venta',monto_total='1.00',fecha_inicio=date(2026,1,1),cuotas=99,primer_vencimiento=date(2026,1,1))
        cid=op.alta_contrato(data,self.db,self.admin)['id_contrato']
        qs=op.cuotas(cid,self.db,self.client)
        self.assertTrue(all(q['monto']>0 for q in qs))
        self.assertEqual(sum(q['monto'] for q in qs),Decimal('1'))
    def test_smtp_uses_client_email_and_pdf(self):
        q=op.cuotas(self.cid,self.db,self.client)[0]
        p=op.pagar(q['id'],op.PagoCuota(monto='10',clave_idempotencia='email-123',confirma_simulacion=True),self.db,self.admin)
        with patch.dict('os.environ',{'SMTP_HOST':'smtp.example.test','SMTP_USER':'sender@example.test','SMTP_PASSWORD':'fake-test-password'}),patch('operaciones.smtplib.SMTP') as smtp:
            result=op.enviar_recibo(p['id_pago'],self.db,self.admin)
            msg=smtp.return_value.__enter__.return_value.send_message.call_args.args[0]
            self.assertEqual(msg['To'],self.client.correo)
            self.assertEqual(list(msg.iter_attachments())[0].get_content_type(),'application/pdf')
            self.assertEqual(result['estado'],'aceptado_por_smtp')
    def test_fcm_reminders_not_duplicated(self):
        op.registrar_token(op.TokenFCM(dispositivo='test',token='z'*40,plataforma='web'),self.db,self.client)
        with patch.dict('os.environ',{'GOOGLE_APPLICATION_CREDENTIALS':'fake-test-path'}),patch('firebase_admin.get_app'),patch('firebase_admin.messaging.send') as send:
            first=op.enviar_avisos(1)
            second=op.enviar_avisos(1)
            self.assertEqual(first['enviados'],3)
            self.assertEqual(second['enviados'],0)
            self.assertEqual(send.call_count,3)

if __name__=='__main__':unittest.main(verbosity=2)


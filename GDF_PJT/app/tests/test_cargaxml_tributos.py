from decimal import Decimal
from unittest.mock import patch
import xml.etree.ElementTree as ET
from importlib import import_module

from django.test import SimpleTestCase

from app.classes.CargaXml import CargaXml

cargaxml_module = import_module('app.classes.CargaXml')


class CargaXmlTributosTestCase(SimpleTestCase):
    """Valida mapeamento tributario extraido do XML para persistencia."""

    def setUp(self):
        self.loader = CargaXml()

    def test_processar_impostos_icms_reducao_e_aliquotas(self):
        imposto_xml = ET.fromstring(
            '''
            <imposto xmlns="http://www.portalfiscal.inf.br/nfe">
                <ICMS>
                    <ICMS20>
                        <orig>0</orig>
                        <CST>20</CST>
                        <pRedBC>33.33</pRedBC>
                        <vBC>1000.00</vBC>
                        <pICMS>18.00</pICMS>
                        <vICMS>120.00</vICMS>
                        <vBCST>200.00</vBCST>
                        <pICMSST>12.00</pICMSST>
                        <vICMSST>24.00</vICMSST>
                        <vBCSTRet>90.00</vBCSTRet>
                        <vICMSSTRet>10.80</vICMSSTRet>
                    </ICMS20>
                </ICMS>
                <IPI>
                    <IPITrib>
                        <CST>50</CST>
                        <vBC>100.00</vBC>
                        <pIPI>5.00</pIPI>
                        <vIPI>5.00</vIPI>
                    </IPITrib>
                </IPI>
                <PIS>
                    <PISAliq>
                        <CST>01</CST>
                        <vBC>100.00</vBC>
                        <pPIS>1.65</pPIS>
                        <vPIS>1.65</vPIS>
                    </PISAliq>
                </PIS>
                <COFINS>
                    <COFINSAliq>
                        <CST>01</CST>
                        <vBC>100.00</vBC>
                        <pCOFINS>7.60</pCOFINS>
                        <vCOFINS>7.60</vCOFINS>
                    </COFINSAliq>
                </COFINS>
            </imposto>
            '''
        )

        with patch.object(cargaxml_module.NFe_ICMS.objects, 'create') as icms_create, \
            patch.object(cargaxml_module.NFe_IPI.objects, 'create') as ipi_create, \
            patch.object(cargaxml_module.NFe_PIS.objects, 'create') as pis_create, \
            patch.object(cargaxml_module.NFe_COFINS.objects, 'create') as cofins_create:
            self.loader._processar_impostos(imposto_xml, produto=object())

            icms_kwargs = icms_create.call_args.kwargs
            self.assertEqual(icms_kwargs['cst'], '20')
            self.assertEqual(icms_kwargs['percentual_reducao'], Decimal('33.33'))
            self.assertEqual(icms_kwargs['aliquota'], Decimal('18.00'))
            self.assertEqual(icms_kwargs['aliquota_st'], Decimal('12.00'))
            self.assertEqual(icms_kwargs['valor_base_st_dest'], Decimal('90.00'))
            self.assertEqual(icms_kwargs['valor_icms_st_dest'], Decimal('10.80'))

            ipi_kwargs = ipi_create.call_args.kwargs
            self.assertEqual(ipi_kwargs['aliquota'], Decimal('5.00'))
            self.assertEqual(ipi_kwargs['valor_ipi'], Decimal('5.00'))

            pis_kwargs = pis_create.call_args.kwargs
            self.assertEqual(pis_kwargs['aliquota'], Decimal('1.65'))
            self.assertEqual(pis_kwargs['valor_base_calculo'], Decimal('100.00'))

            cofins_kwargs = cofins_create.call_args.kwargs
            self.assertEqual(cofins_kwargs['aliquota'], Decimal('7.60'))
            self.assertEqual(cofins_kwargs['valor_base_calculo'], Decimal('100.00'))

    def test_processar_impostos_csosn_e_aliquota_quantidade(self):
        imposto_xml = ET.fromstring(
            '''
            <imposto xmlns="http://www.portalfiscal.inf.br/nfe">
                <ICMS>
                    <ICMSSN900>
                        <orig>0</orig>
                        <CSOSN>900</CSOSN>
                        <pRedBC>10.00</pRedBC>
                        <vBC>500.00</vBC>
                        <pICMS>17.00</pICMS>
                        <vICMS>76.50</vICMS>
                    </ICMSSN900>
                </ICMS>
                <PIS>
                    <PISQtde>
                        <CST>03</CST>
                        <qBCProd>10.0000</qBCProd>
                        <vAliqProd>0.2000</vAliqProd>
                        <vPIS>2.00</vPIS>
                    </PISQtde>
                </PIS>
                <COFINS>
                    <COFINSQtde>
                        <CST>03</CST>
                        <qBCProd>10.0000</qBCProd>
                        <vAliqProd>0.9000</vAliqProd>
                        <vCOFINS>9.00</vCOFINS>
                    </COFINSQtde>
                </COFINS>
            </imposto>
            '''
        )

        with patch.object(cargaxml_module.NFe_ICMS.objects, 'create') as icms_create, \
            patch.object(cargaxml_module.NFe_IPI.objects, 'create') as _ipi_create, \
            patch.object(cargaxml_module.NFe_PIS.objects, 'create') as pis_create, \
            patch.object(cargaxml_module.NFe_COFINS.objects, 'create') as cofins_create:
            self.loader._processar_impostos(imposto_xml, produto=object())

            icms_kwargs = icms_create.call_args.kwargs
            self.assertEqual(icms_kwargs['cst'], '900')
            self.assertEqual(icms_kwargs['percentual_reducao'], Decimal('10.00'))

            pis_kwargs = pis_create.call_args.kwargs
            self.assertEqual(pis_kwargs['aliquota'], Decimal('0'))
            self.assertEqual(pis_kwargs['quantidade_vendida'], Decimal('10.0000'))
            self.assertEqual(pis_kwargs['aliquota_quantidade'], Decimal('0.2000'))

            cofins_kwargs = cofins_create.call_args.kwargs
            self.assertEqual(cofins_kwargs['aliquota'], Decimal('0'))
            self.assertEqual(cofins_kwargs['quantidade_vendida'], Decimal('10.0000'))
            self.assertEqual(cofins_kwargs['aliquota_quantidade'], Decimal('0.9000'))

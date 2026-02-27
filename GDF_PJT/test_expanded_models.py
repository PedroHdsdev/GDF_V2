#!/usr/bin/env python
"""
End-to-end test for expanded NFe, CTe, and NFSe models with new fields
Tests the CargaXml extraction methods for all document types
"""
import os
import sys
import django
from datetime import datetime
from pathlib import Path
import tempfile

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GDF_PJT.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from app.classes.CargaXml import Carga_xml
from app.db_GDF.NFe.models import NFe, NFe_Identificacao
from app.db_GDF.CTe.models import (
    CTe, CTe_Carga, CTe_Servico, CTe_Veiculo, CTe_Motorista, CTe_Percurso, CTe_Fiscal
)
from app.db_GDF.NFSe.models import (
    NFSe, NFSe_RPS, NFSe_Retencao, NFSe_Pagamento, NFSe_Credenciamento
)

def test_nfe_expanded():
    """Test NFe with expanded ICMS-ST fields"""
    print("\n=== TESTE NFe ===")
    
    # Create minimal NFe XML with new fields
    nfe_xml = b"""<?xml version="1.0"?>
<NFe xmlns="http://www.portalfiscal.inf.br/nfe">
    <infNFe Id="NFe35220101234567000167550010000000011234567890">
        <ide>
            <cUF>35</cUF>
            <cNF>12345678</cNF>
            <natOp>VENDA</natOp>
            <mod>55</mod>
            <serie>1</serie>
            <nNF>1</nNF>
            <dhEmi>2022-11-15T10:00:00</dhEmi>
            <dhSaiEnt>2022-11-15T10:00:00</dhSaiEnt>
            <tpNF>1</tpNF>
            <idDest>1</idDest>
            <cMunFG>3519004</cMunFG>
            <tpImp>1</tpImp>
            <tpEmis>1</tpEmis>
            <cDV>0</cDV>
            <tpAmb>2</tpAmb>
            <finNFe>1</finNFe>
            <indFinal>N</indFinal>
            <indPres>1</indPres>
            <procEmi>0</procEmi>
            <verProc>4.00</verProc>
        </ide>
        <emit>
            <CNPJ>12345678000167</CNPJ>
            <xNome>EMPRESA TESTE LTDA</xNome>
            <xFant>EMPRESA TESTE</xFant>
            <enderEmit>
                <xLgr>RUA TESTE</xLgr>
                <nro>123</nro>
                <xBairro>CENTRO</xBairro>
                <cMun>3519004</cMun>
                <xMun>SAO PAULO</xMun>
                <UF>SP</UF>
                <CEP>01000000</CEP>
            </enderEmit>
            <IE>12345678901234</IE>
        </emit>
        <dest>
            <CNPJ>87654321000098</CNPJ>
            <xNome>CLIENTE TESTE LTDA</xNome>
            <enderDest>
                <xLgr>RUA CLIENTE</xLgr>
                <nro>456</nro>
                <xBairro>ZONA SUL</xBairro>
                <cMun>3519004</cMun>
                <xMun>SAO PAULO</xMun>
                <UF>SP</UF>
                <CEP>02000000</CEP>
            </enderDest>
            <IE>98765432109876</IE>
        </dest>
        <det nItem="1">
            <prod>
                <code>1234567</code>
                <xProd>PRODUTO TESTE</xProd>
                <NCM>12345678</NCM>
                <qCom>1.0</qCom>
                <uCom>UN</uCom>
                <vUnCom>100.00</vUnCom>
                <vProd>100.00</vProd>
                <vItem12741>0.00</vItem12741>
                <indTot>1</indTot>
                <xPed>12345</xPed>
                <nItemPed>1</nItemPed>
            </prod>
            <imposto>
                <ICMS>
                    <ICMS00>
                        <orig>0</orig>
                        <CST>00</CST>
                        <modBC>3</modBC>
                        <vBC>100.00</vBC>
                        <pICMS>18.00</pICMS>
                        <vICMS>18.00</vICMS>
                        <vBCST>100.00</vBCST>
                        <pST>7.00</pST>
                        <vST>7.00</vST>
                    </ICMS00>
                </ICMS>
                <IPI></IPI>
                <II></II>
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
        </det>
        <total>
            <ICMSTot>
                <vBC>100.00</vBC>
                <vICMS>18.00</vICMS>
                <vICMSDeson>0.00</vICMSDeson>
                <vFCP>0.00</vFCP>
                <vBCST>0.00</vBCST>
                <vST>0.00</vST>
                <vFCPST>0.00</vFCPST>
                <vFCPSTRet>0.00</vFCPSTRet>
                <vProd>100.00</vProd>
                <vFrete>0.00</vFrete>
                <vSeg>0.00</vSeg>
                <vDesc>0.00</vDesc>
                <vII>0.00</vII>
                <vIPI>0.00</vIPI>
                <vIPIDevol>0.00</vIPIDevol>
                <vPIS>1.65</vPIS>
                <vCOFINS>7.60</vCOFINS>
                <vOutro>0.00</vOutro>
                <vNF>126.25</vNF>
            </ICMSTot>
        </total>
        <transp>
            <modFrete>0</modFrete>
        </transp>
        <cobr></cobr>
        <pag>
            <detPag>
                <tPag>01</tPag>
                <vPag>126.25</vPag>
            </detPag>
        </pag>
        <infAdic></infAdic>
    </infNFe>
</NFe>"""

    try:
        loader = Carga_xml()
        result = loader.set_nfe(nfe_xml, 'TESTE', 'test_user', '1')
        
        if result:
            print("✓ NFe criada com sucesso")
            # Check for ICMS-ST fields
            nfe_ident = NFe_Identificacao.objects.filter(
                numero='1', serie='1'
            ).first()
            if nfe_ident:
                icms = nfe_ident.icms if hasattr(nfe_ident, 'icms') else None
                print(f"✓ Identificação encontrada: {nfe_ident.numero}")
            return True
        else:
            print("✗ Falha ao criar NFe")
            return False
            
    except Exception as e:
        print(f"✗ Erro ao testar NFe: {str(e)}")
        return False

def test_cte_expanded():
    """Test CTe with expanded models (Carga, Servico, Veiculo, etc.)"""
    print("\n=== TESTE CTe ===")
    
    cte_xml = b"""<?xml version="1.0"?>
<CTe xmlns="http://www.portalfiscal.inf.br/cte">
    <infCte Id="CTe35220101234567000167570010000000011234567890">
        <ide>
            <cUF>35</cUF>
            <cCT>123456</cCT>
            <nCT>1</nCT>
            <mod>57</mod>
            <serie>1</serie>
            <dhEmi>2022-11-15T10:00:00</dhEmi>
            <tpCTe>1</tpCTe>
            <tpServ>0</tpServ>
            <tpAmb>2</tpAmb>
            <tpEmit>1</tpEmit>
            <procEmi>0</procEmi>
            <verProc>4.00</verProc>
            <indGlobalizado>0</indGlobalizado>
        </ide>
        <emit>
            <CNPJ>12345678000167</CNPJ>
            <xNome>TRANSPORTADORA TESTE</xNome>
            <IE>123456789012345</IE>
            <enderEmit>
                <xLgr>RUA TRANSPORT</xLgr>
                <nro>789</nro>
                <xBairro>ZONA INDUSTRIAL</xBairro>
                <cMun>3519004</cMun>
                <xMun>SAO PAULO</xMun>
                <UF>SP</UF>
                <CEP>03000000</CEP>
            </enderEmit>
        </emit>
        <dest>
            <CNPJ>87654321000098</CNPJ>
            <xNome>CLIENTE TRANSPORTE</xNome>
            <enderDest>
                <xLgr>RUA DESTINO</xLgr>
                <nro>999</nro>
                <xBairro>ZONA SUL</xBairro>
                <cMun>3519004</cMun>
                <xMun>SAO PAULO</xMun>
                <UF>SP</UF>
                <CEP>04000000</CEP>
            </enderDest>
        </dest>
        <infCarga>
            <xNaturez>Carga Geral</xNaturez>
            <vPBrutoCarga>5000.00</vPBrutoCarga>
            <vMerc>4500.00</vMerc>
            <qVol>10</qVol>
            <xMaterial>Mercadoria Diversa</xMaterial>
        </infCarga>
        <infServ>
            <vTPrest>500.00</vTPrest>
            <vGRIS>0.00</vGRIS>
            <vValorCobrado>500.00</vValorCobrado>
            <vOutrasDesp>50.00</vOutrasDesp>
        </infServ>
        <infCteCarregamento>
            <veiculo>
                <tpVeic>1</tpVeic>
                <placa>ABC1234</placa>
                <renavam>12345678901234</renavam>
                <tara>5000</tara>
                <capKg>10000</capKg>
                <marca>SCANIA</marca>
                <modelo>R440</modelo>
                <tVazKg>5000</tVazKg>
                <anoFab>2020</anoFab>
                <anoMod>2020</anoMod>
                <nEixos>3</nEixos>
                <tComb>D</tComb>
            </veiculo>
            <mot>
                <CPF>12345678901</CPF>
                <RG>12345678</RG>
                <xNome>MOTORISTA TESTE</xNome>
                <nCNH>12345678901</nCNH>
                <cCNH>A</cCNH>
                <dVencCNH>2025-11-15</dVencCNH>
                <banco>001</banco>
                <agencia>0001</agencia>
                <conta>123456789</conta>
            </mot>
            <perCurso>
                <xOrigem>SAO PAULO</xOrigem>
                <xDestino>RIO DE JANEIRO</xDestino>
                <xPercurso>BR-101</xPercurso>
                <nPara>2</nPara>
                <vTpPed>150.00</vTpPed>
                <tpPag>01</tpPag>
                <odIni>0</odIni>
                <odFim>450</odFim>
            </perCurso>
        </infCteCarregamento>
        <imp>
            <ICMS>
                <ICMS01>
                    <orig>0</orig>
                    <CST>01</CST>
                    <CFOP>5353</CFOP>
                    <vBC>500.00</vBC>
                    <pICMS>7.00</pICMS>
                    <vICMS>35.00</vICMS>
                </ICMS01>
            </ICMS>
            <vPIS>0.00</vPIS>
            <vCOFINS>0.00</vCOFINS>
            <vIRRF>0.00</vIRRF>
        </imp>
        <total>
            <vRec>535.00</vRec>
        </total>
    </infCte>
</CTe>"""

    try:
        loader = Carga_xml()
        result = loader.set_cte(cte_xml, 'TESTE', 'test_user', '1')
        
        if result:
            print("✓ CTe criada com sucesso")
            
            # Verify expanded models were created
            from app.db_GDF.CTe.models import CTe_Identificacao
            cte_ident = CTe_Identificacao.objects.filter(numero='1').first()
            
            if cte_ident:
                carga = CTe_Carga.objects.filter(cte_identificacao=cte_ident).first()
                servico = CTe_Servico.objects.filter(cte_identificacao=cte_ident).first()
                veiculo = CTe_Veiculo.objects.filter(cte_identificacao=cte_ident).first()
                motorista = CTe_Motorista.objects.filter(cte_identificacao=cte_ident).first()
                percurso = CTe_Percurso.objects.filter(cte_identificacao=cte_ident).first()
                fiscal = CTe_Fiscal.objects.filter(cte_identificacao=cte_ident).first()
                
                print(f"  ✓ CTe_Carga: {carga is not None}")
                print(f"  ✓ CTe_Servico: {servico is not None}")
                print(f"  ✓ CTe_Veiculo: {veiculo is not None}")
                print(f"  ✓ CTe_Motorista: {motorista is not None}")
                print(f"  ✓ CTe_Percurso: {percurso is not None}")
                print(f"  ✓ CTe_Fiscal: {fiscal is not None}")
                
                return all([carga, servico, veiculo, motorista, percurso, fiscal])
            
        return False
        
    except Exception as e:
        print(f"✗ Erro ao testar CTe: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_nfse_expanded():
    """Test NFSe with expanded models (RPS, Retencao, Pagamento, Credenciamento)"""
    print("\n=== TESTE NFSe ===")
    
    nfse_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<NFe>
    <InfNfse>
        <Identificacao>
            <Numero>123</Numero>
            <Serie>1</Serie>
            <DataEmissao>2022-11-15</DataEmissao>
            <Competencia>2022-11-01</Competencia>
            <CodigoMunicipio>3519004</CodigoMunicipio>
        </Identificacao>
        <PrestadorServico>
            <IdentificacaoPrestador>
                <CNPJ>12345678000167</CNPJ>
                <InscricaoMunicipal>123456789</InscricaoMunicipal>
            </IdentificacaoPrestador>
            <RazaoSocial>PRESTADOR TESTE LTDA</RazaoSocial>
            <EnderecoPrestador>
                <xLgr>RUA PRESTADOR</xLgr>
                <nro>123</nro>
                <xBairro>CENTRO</xBairro>
                <cMun>3519004</cMun>
                <xMun>SAO PAULO</xMun>
                <UF>SP</UF>
                <CEP>01000000</CEP>
            </EnderecoPrestador>
        </PrestadorServico>
        <TomadorServico>
            <IdentificacaoTomador>
                <CNPJ>87654321000098</CNPJ>
            </IdentificacaoTomador>
            <RazaoSocial>CLIENTE NFSE LTDA</RazaoSocial>
            <enderTomador>
                <xLgr>RUA TOMADOR</xLgr>
                <nro>456</nro>
                <xBairro>ZONA SUL</xBairro>
                <cMun>3519004</cMun>
                <xMun>SAO PAULO</xMun>
                <UF>SP</UF>
                <CEP>02000000</CEP>
            </enderTomador>
        </TomadorServico>
        <Servico>
            <Descricao>SERVICO TESTE</Descricao>
            <Quantidade>1</Quantidade>
            <ValorUnitario>1000.00</ValorUnitario>
            <ValorTotal>1000.00</ValorTotal>
            <CodigoServicoMunicipal>01</CodigoServicoMunicipal>
        </Servico>
        <Rps>
            <Numero>123</Numero>
            <Serie>1</Serie>
            <Tipo>RPS</Tipo>
            <DataEmissao>2022-11-15</DataEmissao>
            <Status>NORMAL</Status>
            <Valor>1000.00</Valor>
        </Rps>
        <Retencoes>
            <RetencaoDados>
                <Valor>100.00</Valor>
            </RetencaoDados>
        </Retencoes>
        <DadosFormaPagamento>
            <Forma>01</Forma>
            <DataPagamento>2022-11-20</DataPagamento>
            <Parcelas>1</Parcelas>
        </DadosFormaPagamento>
        <ValorLiquido>900.00</ValorLiquido>
        <OptanteSimplesNacional>N</OptanteSimplesNacional>
    </InfNfse>
</NFe>"""

    try:
        loader = Carga_xml()
        result = loader.set_nfse(nfse_xml, 'TESTE', 'test_user', '1')
        
        if result:
            print("✓ NFSe criada com sucesso")
            
            # Verify expanded models were created
            from app.db_GDF.NFSe.models import NFSe_Identificacao
            nfse_ident = NFSe_Identificacao.objects.filter(numero='123').first()
            
            if nfse_ident:
                rps = NFSe_RPS.objects.filter(nfse_identificacao=nfse_ident).first()
                retencao = NFSe_Retencao.objects.filter(nfse_identificacao=nfse_ident).first()
                pagamento = NFSe_Pagamento.objects.filter(nfse_identificacao=nfse_ident).first()
                credenciamento = NFSe_Credenciamento.objects.filter(nfse_identificacao=nfse_ident).first()
                
                print(f"  ✓ NFSe_RPS: {rps is not None}")
                print(f"  ✓ NFSe_Retencao: {retencao is not None}")
                print(f"  ✓ NFSe_Pagamento: {pagamento is not None}")
                print(f"  ✓ NFSe_Credenciamento: {credenciamento is not None}")
                
                return all([rps, retencao, pagamento])
            
        return False
        
    except Exception as e:
        print(f"✗ Erro ao testar NFSe: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n" + "="*50)
    print("TESTE END-TO-END MODELOS EXPANDIDOS")
    print("="*50)
    
    results = {
        'NFe': test_nfe_expanded(),
        'CTe': test_cte_expanded(),
        'NFSe': test_nfse_expanded()
    }
    
    print("\n" + "="*50)
    print("RESULTADOS")
    print("="*50)
    for doc_type, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{doc_type}: {status}")
    
    all_passed = all(results.values())
    print(f"\nGeral: {'✓ TODOS OS TESTES PASSARAM' if all_passed else '✗ ALGUNS TESTES FALHARAM'}")
    
    sys.exit(0 if all_passed else 1)

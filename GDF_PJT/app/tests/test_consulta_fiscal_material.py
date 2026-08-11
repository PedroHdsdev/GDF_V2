from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from app.utils.consulta_fiscal_material_db import consultar_fiscal_material_db


class ConsultaFiscalMaterialDbTestCase(SimpleTestCase):
    def test_consulta_usa_schema_nfe_e_aplica_filtros(self):
        cursor = MagicMock()
        cursor.description = [
            ("material",),
            ("descricao_material",),
            ("fornecedor",),
            ("aliquota_icms",),
            ("aliquota_st",),
            ("aliquota_cofins",),
            ("aliquota_ipi",),
            ("aliquota_pis",),
            ("reducao_base",),
        ]
        cursor.fetchone.side_effect = [(1,), None]
        cursor.fetchall.return_value = [
            (
                "MAT01",
                "Material 01",
                "Fornecedor LTDA",
                Decimal("18.00"),
                Decimal("12.00"),
                Decimal("7.60"),
                Decimal("5.00"),
                Decimal("1.65"),
                Decimal("33.33"),
            )
        ]

        with patch("app.utils.consulta_fiscal_material_db.connection.cursor") as cursor_factory:
            cursor_factory.return_value.__enter__.return_value = cursor

            result = consultar_fiscal_material_db(
                cod_cliente="1000",
                filtros={
                    "chave_acesso": "CHAVE",
                    "cod_material": "MAT",
                    "fornecedor": "FORN",
                    "data_inicio": "2026-08-01",
                    "data_fim": "2026-08-31",
                },
                page=1,
                page_size=30,
                order="material",
                direction="asc",
            )

        executed_count_sql = cursor.execute.call_args_list[0].args[0]
        executed_count_params = cursor.execute.call_args_list[0].args[1]
        executed_data_sql = cursor.execute.call_args_list[1].args[0]
        executed_data_params = cursor.execute.call_args_list[1].args[1]

        self.assertIn("FROM nfe.nfe_produto p", executed_count_sql)
        self.assertIn("INNER JOIN nfe.nfe_identificacao i", executed_count_sql)
        self.assertIn("INNER JOIN nfe.nfe n", executed_count_sql)
        self.assertIn("LEFT JOIN nfe.nfe_icms ic", executed_data_sql)
        self.assertIn("LEFT JOIN nfe.nfe_cofins cof", executed_data_sql)
        self.assertIn("COALESCE(i.chave_acesso, '') ILIKE", executed_data_sql)
        self.assertIn("n.gdfcliente_id = %s", executed_data_sql)
        self.assertIn("ORDER BY material ASC", executed_data_sql)
        self.assertEqual(executed_count_params[0], "1000")
        self.assertEqual(executed_data_params[0], "1000")
        self.assertEqual(result.total, 1)
        self.assertEqual(result.items[0]["material"], "MAT01")
        self.assertEqual(result.items[0]["reducao_base"], Decimal("33.33"))
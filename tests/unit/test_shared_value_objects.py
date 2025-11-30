# tests/unit/test_shared_value_objects.py
"""
Tests unitarios para Value Objects compartidos.

✅ NUEVO: Tests de Shared Kernel
"""

import pytest
from decimal import Decimal
from datetime import date, datetime

from app.shared.domain.value_objects.moneda import Moneda, CodigoMoneda
from app.shared.domain.value_objects.direccion import Direccion
from app.shared.domain.value_objects.rango_fechas import RangoFechas
from app.shared.domain.value_objects.monto import Monto


class TestMoneda:
    """Tests para Value Object Moneda."""
    
    def test_crear_moneda_desde_codigo(self):
        """Test crear moneda desde código."""
        moneda = Moneda.from_code("USD")
        assert moneda.codigo == "USD"
        assert moneda.simbolo == "$"
        assert moneda.nombre == "Dólar estadounidense"
    
    def test_moneda_invalida(self):
        """Test que moneda inválida lanza error."""
        with pytest.raises(ValueError, match="Código de moneda inválido"):
            Moneda("INVALID")
    
    def test_monedas_iguales(self):
        """Test comparación de monedas."""
        moneda1 = Moneda.from_code("USD")
        moneda2 = Moneda.from_code("USD")
        assert moneda1 == moneda2
        assert hash(moneda1) == hash(moneda2)
    
    def test_monedas_diferentes(self):
        """Test que monedas diferentes no son iguales."""
        moneda1 = Moneda.from_code("USD")
        moneda2 = Moneda.from_code("PEN")
        assert moneda1 != moneda2


class TestDireccion:
    """Tests para Value Object Direccion."""
    
    def test_crear_direccion_valida(self):
        """Test crear dirección válida."""
        direccion = Direccion(
            calle="Av. Principal",
            numero="123",
            ciudad="Lima",
            provincia="Lima",
            pais="Perú"
        )
        assert direccion.calle == "Av. Principal"
        assert direccion.numero == "123"
        assert direccion.ciudad == "Lima"
    
    def test_direccion_invalida_calle_corta(self):
        """Test que calle muy corta lanza error."""
        with pytest.raises(ValueError, match="al menos 3 caracteres"):
            Direccion(calle="AB", ciudad="Lima", pais="Perú")
    
    def test_direccion_completa(self):
        """Test obtener dirección completa."""
        direccion = Direccion(
            calle="Av. Principal",
            numero="123",
            ciudad="Lima",
            pais="Perú"
        )
        completa = direccion.get_direccion_completa()
        assert "Av. Principal 123" in completa
        assert "Lima" in completa
        assert "Perú" in completa


class TestRangoFechas:
    """Tests para Value Object RangoFechas."""
    
    def test_crear_rango_valido(self):
        """Test crear rango válido."""
        fecha_inicio = date(2025, 1, 1)
        fecha_fin = date(2025, 1, 31)
        rango = RangoFechas(fecha_inicio, fecha_fin)
        assert rango.fecha_inicio == fecha_inicio
        assert rango.fecha_fin == fecha_fin
    
    def test_rango_invalido(self):
        """Test que rango inválido lanza error."""
        fecha_inicio = date(2025, 1, 31)
        fecha_fin = date(2025, 1, 1)
        with pytest.raises(ValueError, match="no puede ser mayor"):
            RangoFechas(fecha_inicio, fecha_fin)
    
    def test_contiene_fecha(self):
        """Test verificar si fecha está en rango."""
        rango = RangoFechas(date(2025, 1, 1), date(2025, 1, 31))
        assert rango.contiene_fecha(date(2025, 1, 15)) is True
        assert rango.contiene_fecha(date(2025, 2, 1)) is False
    
    def test_dias_duracion(self):
        """Test calcular duración en días."""
        rango = RangoFechas(date(2025, 1, 1), date(2025, 1, 31))
        assert rango.dias_duracion() == 31


class TestMonto:
    """Tests para Value Object Monto."""
    
    def test_crear_monto_valido(self):
        """Test crear monto válido."""
        moneda = Moneda.from_code("PEN")
        monto = Monto(Decimal("100.50"), moneda)
        assert monto.valor == Decimal("100.50")
        assert monto.moneda == moneda
    
    def test_monto_negativo(self):
        """Test que monto negativo lanza error."""
        moneda = Moneda.from_code("PEN")
        with pytest.raises(ValueError, match="no puede ser negativo"):
            Monto(Decimal("-100"), moneda)
    
    def test_sumar_montos(self):
        """Test sumar dos montos."""
        moneda = Moneda.from_code("PEN")
        monto1 = Monto(Decimal("100"), moneda)
        monto2 = Monto(Decimal("50"), moneda)
        resultado = monto1.sumar(monto2)
        assert resultado.valor == Decimal("150")
    
    def test_sumar_montos_diferentes_monedas(self):
        """Test que sumar montos de diferentes monedas lanza error."""
        monto1 = Monto(Decimal("100"), Moneda.from_code("USD"))
        monto2 = Monto(Decimal("50"), Moneda.from_code("PEN"))
        with pytest.raises(ValueError, match="diferentes monedas"):
            monto1.sumar(monto2)
    
    def test_formatear_monto(self):
        """Test formatear monto."""
        moneda = Moneda.from_code("PEN")
        monto = Monto(Decimal("1234.56"), moneda)
        formateado = monto.formatear()
        assert "S/" in formateado
        assert "1,234.56" in formateado


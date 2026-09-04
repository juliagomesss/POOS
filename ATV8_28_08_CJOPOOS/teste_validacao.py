"""Script para testar a validação de CPF e CNPJ."""
from validador import Validador  # Mudou de validators para validador

print("=" * 60)
print("TESTE DE VALIDAÇÃO DE CPF E CNPJ")
print("=" * 60)

# Testes com CPF
print("\n▶ TESTANDO CPF:")
print("-" * 40)

cpfs_teste = [
    ("529.982.247-25", "Válido", True),
    ("123.456.789-09", "Válido", True),
    ("111.111.111-11", "Inválido", False),
    ("000.000.000-00", "Inválido", False),
]

for cpf, desc, esperado in cpfs_teste:
    resultado = Validador.validar_cpf(cpf)
    status = "✅ PASSOU" if resultado == esperado else "❌ FALHOU"
    print(f"  {cpf}: {status} (Resultado: {resultado}, Esperado: {esperado})")

# Testes com CNPJ
print("\n▶ TESTANDO CNPJ:")
print("-" * 40)

cnpjs_teste = [
    ("12.345.678/0001-90", "Válido", True),
    ("98.765.432/0001-10", "Válido", True),
    ("45.678.901/0001-23", "Válido", True),
    ("34.567.890/0001-45", "Válido", True),
    ("11.111.111/1111-11", "Inválido", False),
    ("00.000.000/0000-00", "Inválido", False),
    ("12.345.678/0001-99", "Inválido", False),
]

for cnpj, desc, esperado in cnpjs_teste:
    resultado = Validador.validar_cnpj(cnpj)
    status = "✅ PASSOU" if resultado == esperado else "❌ FALHOU"
    print(f"  {cnpj}: {status} (Resultado: {resultado}, Esperado: {esperado})")

# Teste automático
print("\n▶ TESTE AUTOMÁTICO (CPF/CNPJ):")
print("-" * 40)

testes_auto = [
    ("529.982.247-25", "CPF", True),
    ("12.345.678/0001-90", "CNPJ", True),
    ("111.111.111-11", "CPF", False),
    ("11.111.111/1111-11", "CNPJ", False),
]

for valor, tipo, esperado in testes_auto:
    valido, tipo_encontrado = Validador.validar_cpf_cnpj(valor)
    status = "✅ PASSOU" if (valido == esperado and tipo == tipo_encontrado) else "❌ FALHOU"
    print(f"  {valor}: {status} (Tipo: {tipo_encontrado}, Válido: {valido})")

print("\n" + "=" * 60)
print("TESTE CONCLUÍDO!")
print("=" * 60)
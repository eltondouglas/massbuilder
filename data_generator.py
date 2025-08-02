# data_generator.py
# Camada de Lógica: responsável por toda a geração de dados.
# Este módulo não depende e não sabe nada sobre a interface gráfica (tkinter).

import csv
import random
import string
import datetime
import uuid
from utils import LISTA_NOMES, LISTA_SOBRENOMES  # Importa as listas do nosso módulo de utilitários

# Tenta importar exrex. Se falhar, levanta um erro que será pego pela GUI.
try:
    import exrex
except ImportError:
    raise ImportError("A biblioteca 'exrex' é necessária. Instale-a com: pip install exrex")


def _criar_valor_atomico(campo):
    """Gera um único valor com base no tipo e limites."""
    tipo = campo.get('tipo', 'string')

    if tipo == 'nome_pessoa':
        nome = random.choice(LISTA_NOMES)
        num_sobrenomes = random.randint(1, 2)
        sobrenomes_escolhidos = random.sample(LISTA_SOBRENOMES, num_sobrenomes)
        return f"{nome} {' '.join(sobrenomes_escolhidos)}"

    try:
        if tipo == 'integer': return random.randint(int(campo['limite'][0]), int(campo['limite'][1]))
        if tipo == 'float': return round(random.uniform(float(campo['limite'][0]), float(campo['limite'][1])), 2)
        if tipo == 'string': return ''.join(random.choice(string.ascii_letters + string.digits) for _ in
                                            range(random.randint(int(campo['limite'][0]), int(campo['limite'][1]))))
        if tipo == 'boolean': return random.choice([True, False])
        if tipo == 'datetime':
            start_date = datetime.datetime.strptime(campo['limite'][0], '%Y-%m-%d')
            end_date = datetime.datetime.strptime(campo['limite'][1], '%Y-%m-%d')
            delta = end_date - start_date
            return (start_date + datetime.timedelta(days=random.randint(0, delta.days))).strftime('%Y-%m-%d %H:%M:%S')
        if tipo == 'uuid': return str(uuid.uuid4())
        if tipo == 'lista_opcoes': return random.choice(campo['opcoes']) if campo.get('opcoes') else None
        if tipo == 'regex': return exrex.getone(campo.get('regex_pattern', '.*'))
    except ValueError as e:
        raise ValueError(f"Parâmetro inválido para o campo '{campo['nome']}' do tipo '{tipo}': {e}")
    except Exception as e:
        raise ValueError(f"Erro ao gerar valor para o campo '{campo['nome']}': {e}")

    return None


def _criar_gerador_de_campo(campo_config, total_linhas):
    """Cria um gerador (iterator) para um campo, respeitando as regras de repetição."""
    tipo, repetir_valor, valores_usados = campo_config.get('tipo', 'string'), campo_config.get('repeticao', 0), set()

    def _gerar_novo_valor():
        for _ in range(total_linhas * 5):  # Limite de tentativas para evitar loops infinitos
            valor = _criar_valor_atomico(campo_config)
            if repetir_valor != 1 or valor not in valores_usados:
                valores_usados.add(valor)
                return valor
        raise ValueError(
            f"Não foi possível gerar valor único para '{campo_config['nome']}'. Verifique se o intervalo/opções são suficientes.")

    if repetir_valor == 0:
        for _ in range(total_linhas): yield _criar_valor_atomico(campo_config)
    else:
        for i in range(total_linhas):
            if i % repetir_valor == 0: valor_atual = _gerar_novo_valor()
            yield valor_atual


def generate_from_config(configuracoes):
    """Função principal que orquestra a geração de dados a partir de um dicionário de configuração."""
    nome_arquivo, num_linhas, campos_cfg, separador, codificacao, regras_sort = \
        configuracoes.get('nome_arquivo'), configuracoes.get('num_linhas'), \
            configuracoes.get('campos'), configuracoes.get('separador'), \
            configuracoes.get('codificacao'), configuracoes.get('regras_sort')

    if not nome_arquivo.lower().endswith('.csv'): nome_arquivo += '.csv'

    # Validações prévias
    for campo in campos_cfg:
        if campo.get('repeticao') == 1:
            if campo['tipo'] == 'integer' and (int(campo['limite'][1]) - int(campo['limite'][0]) + 1) < num_linhas:
                raise ValueError(
                    f"Campo '{campo['nome']}': Intervalo insuficiente para gerar {num_linhas} valores únicos.")
            elif campo['tipo'] == 'lista_opcoes' and len(campo['opcoes']) < num_linhas:
                raise ValueError(
                    f"Campo '{campo['nome']}': Nº de opções insuficiente para gerar {num_linhas} valores únicos.")

    cabecalho = [c['nome'] for c in campos_cfg]
    geradores = [_criar_gerador_de_campo(c, num_linhas) for c in campos_cfg]

    # Modo inteligente de geração baseado na necessidade de ordenação
    if regras_sort:
        # Modo com ordenação (Usa mais RAM)
        dados_em_memoria = [[next(g) for g in geradores] for _ in range(num_linhas)]

        indices_sort = {nome: i for i, nome in enumerate(cabecalho)}
        for regra in reversed(regras_sort):
            nome_campo, ordem_desc = regra['campo'], regra['ordem'] == 'Descendente'
            if nome_campo in indices_sort:
                dados_em_memoria.sort(key=lambda row: row[indices_sort[nome_campo]], reverse=ordem_desc)

        with open(nome_arquivo, 'w', newline='', encoding=codificacao) as file:
            writer = csv.writer(file, delimiter=separador)
            writer.writerow(cabecalho)
            writer.writerows(dados_em_memoria)
    else:
        # Modo sem ordenação (Eficiente em memória)
        with open(nome_arquivo, 'w', newline='', encoding=codificacao) as file:
            writer = csv.writer(file, delimiter=separador)
            writer.writerow(cabecalho)
            for _ in range(num_linhas):
                writer.writerow([next(g) for g in geradores])
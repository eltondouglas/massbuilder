# data_generator.py
# Camada de Lógica: reescrita para lidar com múltiplos arquivos e dependências.

import csv
import random
import string
import datetime
import uuid
from utils import LISTA_NOMES, LISTA_SOBRENOMES

try:
    import exrex
except ImportError:
    raise ImportError("A biblioteca 'exrex' é necessária. Instale-a com: pip install exrex")


def _criar_valor_atomico(campo, chaves_geradas=None):
    """Gera um único valor. Agora pode receber um dicionário de chaves primárias geradas."""
    tipo = campo.get('tipo', 'string')

    if tipo == 'chave_estrangeira':
        arquivo_origem = campo['fk_arquivo']
        campo_origem = campo['fk_campo']
        pk_disponiveis = chaves_geradas.get(arquivo_origem, {}).get(campo_origem)
        if not pk_disponiveis:
            raise ValueError(
                f"Nenhuma chave primária encontrada para {arquivo_origem}.{campo_origem}. Gere o arquivo de origem primeiro.")
        return random.choice(pk_disponiveis)

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


def _criar_gerador_de_campo(campo_config, total_linhas, chaves_geradas):
    """Cria um gerador (iterator) para um campo, com acesso às chaves já geradas."""
    repetir_valor = 1 if campo_config.get('e_pk') else campo_config.get('repeticao', 0)
    valores_usados = set()

    def _gerar_novo_valor():
        for _ in range(total_linhas * 5):
            valor = _criar_valor_atomico(campo_config, chaves_geradas)
            if repetir_valor != 1 or valor not in valores_usados:
                valores_usados.add(valor)
                return valor
        raise ValueError(
            f"Não foi possível gerar valor único para '{campo_config['nome']}'. Verifique o intervalo/opções.")

    if repetir_valor == 0:
        for _ in range(total_linhas): yield _criar_valor_atomico(campo_config, chaves_geradas)
    else:
        for i in range(total_linhas):
            if i % repetir_valor == 0: valor_atual = _gerar_novo_valor()
            yield valor_atual


def generate_from_config(configuracoes):
    """Orquestra a geração de múltiplos arquivos, respeitando as dependências."""
    arquivos_config = configuracoes['arquivos']
    ordem_de_geracao = _resolver_ordem_dependencias(arquivos_config)

    chaves_primarias_geradas = {}  # Dicionário para armazenar todas as PKs geradas

    for nome_arquivo_para_gerar in ordem_de_geracao:
        config_arquivo = next(ac for ac in arquivos_config if ac['nome_arquivo'] == nome_arquivo_para_gerar)

        num_linhas = config_arquivo.get('num_linhas', 100)
        campos_cfg = config_arquivo.get('campos', [])
        separador = config_arquivo.get('separador', ',')
        codificacao = config_arquivo.get('codificacao', 'utf-8')
        regras_sort = config_arquivo.get('regras_sort', [])

        # Validações prévias
        for campo in campos_cfg:
            if campo.get('e_pk') or campo.get('repeticao') == 1:
                if campo['tipo'] == 'integer' and (int(campo['limite'][1]) - int(campo['limite'][0]) + 1) < num_linhas:
                    raise ValueError(
                        f"Arquivo '{nome_arquivo_para_gerar}', Campo '{campo['nome']}': Intervalo insuficiente para gerar {num_linhas} valores únicos.")
                elif campo['tipo'] == 'lista_opcoes' and len(campo['opcoes']) < num_linhas:
                    raise ValueError(
                        f"Arquivo '{nome_arquivo_para_gerar}', Campo '{campo['nome']}': Nº de opções insuficiente para gerar {num_linhas} valores únicos.")

        cabecalho = [c['nome'] for c in campos_cfg]
        geradores = [_criar_gerador_de_campo(c, num_linhas, chaves_primarias_geradas) for c in campos_cfg]

        # Gera todos os dados para o arquivo atual em memória
        dados_em_memoria = [[next(g) for g in geradores] for _ in range(num_linhas)]

        # Armazena as chaves primárias geradas deste arquivo
        chaves_primarias_geradas[nome_arquivo_para_gerar] = {}
        for i, campo in enumerate(campos_cfg):
            if campo.get('e_pk'):
                pk_vals = [row[i] for row in dados_em_memoria]
                chaves_primarias_geradas[nome_arquivo_para_gerar][campo['nome']] = pk_vals

        # Ordenação
        if regras_sort:
            indices_sort = {nome: i for i, nome in enumerate(cabecalho)}
            for regra in reversed(regras_sort):
                nome_campo, ordem_desc = regra['campo'], regra['ordem'] == 'Descendente'
                if nome_campo in indices_sort:
                    dados_em_memoria.sort(key=lambda row: row[indices_sort[nome_campo]], reverse=ordem_desc)

        # Escrita no arquivo
        arquivo_final = nome_arquivo_para_gerar
        if not arquivo_final.lower().endswith('.csv'): arquivo_final += '.csv'
        with open(arquivo_final, 'w', newline='', encoding=codificacao) as file:
            writer = csv.writer(file, delimiter=separador)
            writer.writerow(cabecalho)
            writer.writerows(dados_em_memoria)


def _resolver_ordem_dependencias(arquivos_config):
    """Determina a ordem correta de geração dos arquivos usando um grafo de dependência."""
    nomes_arquivos = {ac['nome_arquivo'] for ac in arquivos_config}
    dependencias = {ac['nome_arquivo']: set() for ac in arquivos_config}

    for ac in arquivos_config:
        for campo in ac['campos']:
            if campo['tipo'] == 'chave_estrangeira':
                if campo['fk_arquivo'] in nomes_arquivos:
                    dependencias[ac['nome_arquivo']].add(campo['fk_arquivo'])

    # Ordenação topológica simples
    ordem_geracao = []
    while len(ordem_geracao) < len(nomes_arquivos):
        arquivos_prontos = [nome for nome, deps in dependencias.items() if not deps]
        if not arquivos_prontos:
            raise ValueError("Dependência circular detectada entre os arquivos. Verifique suas chaves estrangeiras.")

        for nome in arquivos_prontos:
            ordem_geracao.append(nome)
            del dependencias[nome]
            # Remove a dependência resolvida dos outros arquivos
            for _, deps in dependencias.items():
                deps.discard(nome)

    return ordem_geracao


def run_generation_in_thread(config, result_queue):
    """Função 'worker' que é executada na thread de trabalho."""
    try:
        generate_from_config(config)
        result_queue.put({'status': 'success', 'message': f"Arquivos gerados com sucesso!"})
    except Exception as e:
        result_queue.put({'status': 'error', 'message': str(e)})
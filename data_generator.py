# data_generator.py
# Camada de Lógica: atualizada para lidar com constraints de unicidade composta.

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
    # (Sem alterações)
    tipo = campo.get('tipo', 'string')
    if tipo == 'chave_estrangeira':
        arquivo_origem, campo_origem = campo['fk_arquivo'], campo['fk_campo']
        pk_disponiveis = chaves_geradas.get(arquivo_origem, {}).get(campo_origem)
        if not pk_disponiveis: raise ValueError(
            f"Nenhuma chave primária encontrada para {arquivo_origem}.{campo_origem}.")
        return random.choice(pk_disponiveis)
    if tipo == 'nome_pessoa':
        nome, num_sobrenomes = random.choice(LISTA_NOMES), random.randint(1, 2)
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
            return (start_date + datetime.timedelta(days=random.randint(0, (end_date - start_date).days))).strftime(
                '%Y-%m-%d %H:%M:%S')
        if tipo == 'uuid': return str(uuid.uuid4())
        if tipo == 'lista_opcoes': return random.choice(campo['opcoes']) if campo.get('opcoes') else None
        if tipo == 'regex': return exrex.getone(campo.get('regex_pattern', '.*'))
    except ValueError as e:
        raise ValueError(f"Parâmetro inválido para o campo '{campo['nome']}' do tipo '{tipo}': {e}")
    except Exception as e:
        raise ValueError(f"Erro ao gerar valor para o campo '{campo['nome']}': {e}")
    return None


def _criar_gerador_de_campo(campo_config, total_linhas, chaves_geradas):
    # (Sem alterações)
    tipo = campo_config.get('tipo', 'string')
    if tipo == 'chave_estrangeira':
        arquivo_origem, campo_origem = campo_config['fk_arquivo'], campo_config['fk_campo']
        pk_disponiveis = chaves_geradas.get(arquivo_origem, {}).get(campo_origem, [])
        if campo_config.get('cardinalidade') == 'Um-para-Um (1:1)':
            chaves_para_usar = list(pk_disponiveis);
            random.shuffle(chaves_para_usar)
            for _ in range(total_linhas):
                if not chaves_para_usar: raise ValueError(
                    "Não há chaves primárias únicas suficientes para a relação 1:1.")
                yield chaves_para_usar.pop()
            return
        else:  # Um-para-Muitos
            for _ in range(total_linhas): yield random.choice(pk_disponiveis)
            return
    repetir_valor = 1 if campo_config.get('e_pk') else campo_config.get('repeticao', 0)
    valores_usados = set()

    def _gerar_novo_valor():
        for _ in range(total_linhas * 5):
            valor = _criar_valor_atomico(campo_config, chaves_geradas)
            if repetir_valor != 1 or valor not in valores_usados: valores_usados.add(valor); return valor
        raise ValueError(f"Não foi possível gerar valor único para '{campo_config['nome']}'.")

    if repetir_valor == 0:
        for _ in range(total_linhas): yield _criar_valor_atomico(campo_config, chaves_geradas)
    else:
        for i in range(total_linhas):
            if i % repetir_valor == 0: valor_atual = _gerar_novo_valor()
            yield valor_atual


def generate_from_config(configuracoes):
    arquivos_config = configuracoes['arquivos']
    ordem_de_geracao = _resolver_ordem_dependencias(arquivos_config)
    mapa_configs = {ac['nome_arquivo']: ac for ac in arquivos_config}

    # Validação de cardinalidade 1:1
    for config_arquivo in arquivos_config:
        for campo in config_arquivo['campos']:
            if campo.get('cardinalidade') == 'Um-para-Um (1:1)':
                arquivo_pai_nome = campo.get('fk_arquivo')
                if arquivo_pai_nome in mapa_configs and config_arquivo['num_linhas'] > mapa_configs[arquivo_pai_nome][
                    'num_linhas']:
                    raise ValueError(
                        f"Erro de Cardinalidade (1:1): Arquivo '{config_arquivo['nome_arquivo']}' não pode ter mais linhas que '{arquivo_pai_nome}'.")

    chaves_primarias_geradas = {}
    for nome_arquivo_para_gerar in ordem_de_geracao:
        config_arquivo = mapa_configs[nome_arquivo_para_gerar]
        num_linhas, campos_cfg, separador, codificacao, regras_sort = \
            config_arquivo['num_linhas'], config_arquivo['campos'], config_arquivo['separador'], \
                config_arquivo['codificacao'], config_arquivo['regras_sort']

        # Validações...
        cabecalho = [c['nome'] for c in campos_cfg]

        # <<< LÓGICA DE GERAÇÃO COM CONSTRAINT DE UNICIDADE >>>
        dados_em_memoria = []
        constraint_campos = config_arquivo.get('constraint_unicidade', [])
        if constraint_campos:
            constraint_indices = [cabecalho.index(nome) for nome in constraint_campos]
            combinacoes_geradas = set()
            max_tentativas = num_linhas * 20  # Proteção contra loop infinito
            tentativas = 0

            # Recria geradores para cada tentativa, para não esgotar geradores 1:1
            while len(dados_em_memoria) < num_linhas and tentativas < max_tentativas:
                geradores = [_criar_gerador_de_campo(c, 1, chaves_primarias_geradas) for c in campos_cfg]
                nova_linha = [next(g) for g in geradores]
                combinacao = tuple(nova_linha[i] for i in constraint_indices)

                if combinacao not in combinacoes_geradas:
                    combinacoes_geradas.add(combinacao)
                    dados_em_memoria.append(nova_linha)
                tentativas += 1

            if len(dados_em_memoria) < num_linhas:
                raise ValueError(
                    f"Arquivo '{nome_arquivo_para_gerar}': Não foi possível gerar {num_linhas} linhas com a constraint de unicidade solicitada após {max_tentativas} tentativas.")
        else:
            # Geração padrão sem constraint
            geradores = [_criar_gerador_de_campo(c, num_linhas, chaves_primarias_geradas) for c in campos_cfg]
            dados_em_memoria = [[next(g) for g in geradores] for _ in range(num_linhas)]

        chaves_primarias_geradas[nome_arquivo_para_gerar] = {}
        for i, campo in enumerate(campos_cfg):
            if campo.get('e_pk'): chaves_primarias_geradas[nome_arquivo_para_gerar][campo['nome']] = [row[i] for row in
                                                                                                      dados_em_memoria]

        if regras_sort:
            indices_sort = {nome: i for i, nome in enumerate(cabecalho)}
            for regra in reversed(regras_sort):
                nome_campo, ordem_desc = regra['campo'], regra['ordem'] == 'Descendente'
                if nome_campo in indices_sort: dados_em_memoria.sort(key=lambda row: row[indices_sort[nome_campo]],
                                                                     reverse=ordem_desc)

        arquivo_final = nome_arquivo_para_gerar
        if not arquivo_final.lower().endswith('.csv'): arquivo_final += '.csv'
        with open(arquivo_final, 'w', newline='', encoding=codificacao) as file:
            writer = csv.writer(file, delimiter=separador);
            writer.writerow(cabecalho);
            writer.writerows(dados_em_memoria)


def _resolver_ordem_dependencias(arquivos_config):
    # (Sem alterações)
    nomes_arquivos = {ac['nome_arquivo'] for ac in arquivos_config}
    dependencias = {ac['nome_arquivo']: set() for ac in arquivos_config}
    for ac in arquivos_config:
        for campo in ac['campos']:
            if campo['tipo'] == 'chave_estrangeira':
                if campo['fk_arquivo'] in nomes_arquivos: dependencias[ac['nome_arquivo']].add(campo['fk_arquivo'])
    ordem_geracao = []
    while len(ordem_geracao) < len(nomes_arquivos):
        arquivos_prontos = [nome for nome, deps in dependencias.items() if not deps]
        if not arquivos_prontos: raise ValueError("Dependência circular detectada entre os arquivos.")
        for nome in sorted(arquivos_prontos):
            ordem_geracao.append(nome)
            del dependencias[nome]
            for _, deps in dependencias.items(): deps.discard(nome)
    return ordem_geracao


def run_generation_in_thread(config, result_queue):
    # (Sem alterações)
    try:
        generate_from_config(config)
        result_queue.put({'status': 'success', 'message': f"Arquivos gerados com sucesso!"})
    except Exception as e:
        result_queue.put({'status': 'error', 'message': str(e)})
# data_generator.py

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


def _criar_valor_atomico(campo, chaves_geradas=None, linha_atual=None):
    """Gera um único valor. Pode receber contexto da linha atual e chaves geradas."""
    tipo = campo.get('tipo', 'string')

    if tipo == 'Nulo/Vazio': return ''
    if tipo == 'Valor Fixo': return campo.get('valor_fixo', '')
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
    except (ValueError, KeyError) as e:
        raise ValueError(
            f"Parâmetro inválido ou ausente para o campo '{campo.get('nome', 'Desconhecido')}' do tipo '{tipo}': {e}")
    except Exception as e:
        raise ValueError(f"Erro ao gerar valor para o campo '{campo.get('nome', 'Desconhecido')}': {e}")
    return None


def _criar_gerador_de_campo(campo_config, total_linhas, chaves_geradas):
    """Cria um gerador (iterator) para um campo, respeitando as regras de repetição e cardinalidade."""
    tipo = campo_config.get('tipo', 'string')

    if tipo == 'chave_estrangeira':
        arquivo_origem, campo_origem = campo_config['fk_arquivo'], campo_config['fk_campo']
        pk_disponiveis = chaves_geradas.get(arquivo_origem, {}).get(campo_origem, [])

        if campo_config.get('cardinalidade') == 'Um-para-Um (1:1)':
            chaves_para_usar = list(pk_disponiveis)
            random.shuffle(chaves_para_usar)
            for _ in range(total_linhas):
                if not chaves_para_usar: raise ValueError(
                    "Não há chaves primárias únicas suficientes para a relação 1:1.")
                yield chaves_para_usar.pop()
            return
        else:  # Padrão é Um-para-Muitos (1:N)
            if not pk_disponiveis:
                # Retorna um gerador vazio se não houver chaves, evitando erro
                for _ in range(total_linhas): yield None
                return
            for _ in range(total_linhas):
                yield random.choice(pk_disponiveis)
            return

    # Lógica padrão para outros tipos de campo
    repetir_valor = 1 if campo_config.get('e_pk') else campo_config.get('repeticao', 0)
    valores_usados = set()

    def _gerar_novo_valor():
        for _ in range(total_linhas * 5):
            valor = _criar_valor_atomico(campo_config, chaves_geradas)
            if repetir_valor != 1 or valor not in valores_usados:
                valores_usados.add(valor)
                return valor
        raise ValueError(f"Não foi possível gerar valor único para '{campo_config['nome']}'.")

    if repetir_valor == 0:
        for _ in range(total_linhas): yield _criar_valor_atomico(campo_config, chaves_geradas)
    else:
        for i in range(total_linhas):
            if i % repetir_valor == 0: valor_atual = _gerar_novo_valor()
            yield valor_atual


def _avaliar_condicao(valor_campo_ref, operador, valor_condicao):
    """Avalia uma condição e retorna True ou False."""
    try:
        if operador in ['>', '<', '>=', '<=']:
            val_ref_num, val_cond_num = float(valor_campo_ref), float(valor_condicao)
            if operador == '>': return val_ref_num > val_cond_num
            if operador == '<': return val_ref_num < val_cond_num
            if operador == '>=': return val_ref_num >= val_cond_num
            if operador == '<=': return val_ref_num <= val_cond_num

        val_ref_str, val_cond_str = str(valor_campo_ref), str(valor_condicao)
        if operador == 'é igual a': return val_ref_str == val_cond_str
        if operador == 'é diferente de': return val_ref_str != val_cond_str
        if operador == 'contém': return val_cond_str in val_ref_str
        if operador == 'não contém': return val_cond_str not in val_ref_str
    except (ValueError, TypeError):
        return False
    return False


def generate_from_config(configuracoes):
    arquivos_config = configuracoes['arquivos']
    ordem_arquivos = _resolver_ordem_dependencias(arquivos_config)
    mapa_configs = {ac['nome_arquivo']: ac for ac in arquivos_config}
    chaves_primarias_geradas = {}

    for nome_arquivo in ordem_arquivos:
        config = mapa_configs[nome_arquivo]
        num_linhas, campos_cfg, separador, codificacao, regras_sort, constraint_unicidade = \
            config['num_linhas'], config['campos'], config['separador'], config['codificacao'], \
                config['regras_sort'], config.get('constraint_unicidade', [])

        ordem_campos = _resolver_ordem_campos(campos_cfg)
        mapa_campos = {c['nome']: c for c in campos_cfg}

        # Cria geradores de estado (para repetição, 1:1, etc)
        geradores_estado = {c['nome']: _criar_gerador_de_campo(c, num_linhas, chaves_primarias_geradas) for c in
                            campos_cfg}

        dados_em_memoria = []
        combinacoes_geradas = set()
        max_tentativas = num_linhas * 20
        tentativas = 0

        while len(dados_em_memoria) < num_linhas and tentativas < max_tentativas:
            linha_atual = {}
            for nome_campo in ordem_campos:
                campo_cfg = mapa_campos[nome_campo]

                regra = campo_cfg.get('condicional')

                if regra and regra.get('campo_ref') in linha_atual:
                    condicao_ok = _avaliar_condicao(linha_atual[regra['campo_ref']], regra['operador'],
                                                    regra['valor_ref'])
                    acao = regra['acao_verdadeiro'] if condicao_ok else regra['acao_falso']

                    if acao.get('tipo') == 'Usar Geração Padrão':
                        valor_gerado = next(geradores_estado[nome_campo])
                    else:
                        valor_gerado = _criar_valor_atomico(acao, chaves_primarias_geradas, linha_atual)
                else:
                    valor_gerado = next(geradores_estado[nome_campo])

                linha_atual[nome_campo] = valor_gerado

            if constraint_unicidade:
                combinacao = tuple(linha_atual[nome] for nome in constraint_unicidade)
                if combinacao in combinacoes_geradas:
                    tentativas += 1
                    # Recria os geradores para a próxima tentativa, para não esgotar geradores 1:1
                    geradores_estado = {c['nome']: _criar_gerador_de_campo(c, num_linhas - len(dados_em_memoria),
                                                                           chaves_primarias_geradas) for c in
                                        campos_cfg}
                    continue
                combinacoes_geradas.add(combinacao)

            dados_em_memoria.append(linha_atual)
            tentativas += 1

        if len(dados_em_memoria) < num_linhas:
            raise ValueError(
                f"Arquivo '{nome_arquivo}': Não foi possível gerar {num_linhas} linhas com as constraints de unicidade.")

        cabecalho = [c['nome'] for c in campos_cfg]
        dados_finais = [[linha[nome_campo] for nome_campo in cabecalho] for linha in dados_em_memoria]

        chaves_primarias_geradas[nome_arquivo] = {}
        for i, campo in enumerate(campos_cfg):
            if campo.get('e_pk'):
                chaves_primarias_geradas[nome_arquivo][campo['nome']] = [row[i] for row in dados_finais]

        if regras_sort:
            indices_sort = {nome: i for i, nome in enumerate(cabecalho)}
            for regra in reversed(regras_sort):
                nome_campo, ordem_desc = regra['campo'], regra['ordem'] == 'Descendente'
                if nome_campo in indices_sort:
                    dados_finais.sort(key=lambda row: row[indices_sort[nome_campo]], reverse=ordem_desc)

        arquivo_final = nome_arquivo
        if not arquivo_final.lower().endswith('.csv'): arquivo_final += '.csv'
        with open(arquivo_final, 'w', newline='', encoding=codificacao) as file:
            writer = csv.writer(file, delimiter=separador)
            writer.writerow(cabecalho)
            writer.writerows(dados_finais)


def _resolver_ordem_campos(campos_cfg):
    nomes_campos = [c['nome'] for c in campos_cfg]
    dependencias = {c['nome']: set() for c in campos_cfg}
    for c in campos_cfg:
        regra = c.get('condicional')
        if regra and regra.get('campo_ref') in nomes_campos:
            # Garante que a dependência seja apenas se o campo de referência existir
            if regra['campo_ref'] != c['nome']:
                dependencias[c['nome']].add(regra['campo_ref'])

    ordem_geracao = []
    while len(ordem_geracao) < len(nomes_campos):
        campos_prontos = [nome for nome, deps in dependencias.items() if not deps]
        if not campos_prontos: raise ValueError("Dependência circular detectada entre os campos.")
        for nome in sorted(campos_prontos):
            ordem_geracao.append(nome)
            del dependencias[nome]
            for _, deps in dependencias.items(): deps.discard(nome)
    return ordem_geracao


def _resolver_ordem_dependencias(arquivos_config):
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
    try:
        generate_from_config(config)
        result_queue.put(
            {'status': 'success', 'message': f"Arquivos gerados com sucesso!"})
    except Exception as e:
        result_queue.put({'status': 'error', 'message': str(e)})
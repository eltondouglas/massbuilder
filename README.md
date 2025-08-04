# MassBuilder V0.5.1

## Visão Geral

O **MassBuilder** é uma ferramenta de desktop robusta, construída em Python com a biblioteca Tkinter, projetada para a criação de massas de dados complexas e customizáveis. É a solução ideal para equipes de desenvolvimento e QA que precisam popular bancos de dados para testes, criar arquivos para simulações ou gerar datasets para análise.

A aplicação possui uma arquitetura modular e multi-thread, garantindo que a interface permaneça responsiva mesmo durante o processamento de grandes volumes de dados.

## Principais Funcionalidades

- **Interface Gráfica Intuitiva:** Gerencie todas as configurações através de uma GUI limpa e organizada.
- **Geração Multi-Arquivo:** Crie múltiplos arquivos CSV em uma única sessão, utilizando um sistema de abas.
- **Dados Relacionais (PK/FK):** Defina colunas como Chaves Primárias (PK) e crie Chaves Estrangeiras (FK) em outros arquivos para gerar dados consistentes e relacionados.
- **Controle de Cardinalidade:** Especifique a natureza dos relacionamentos como **Um-para-Um (1:1)** ou **Um-para-Muitos (1:N)**.
- **Geração Condicional:** Implemente regras de negócio complexas (lógica SE/ENTÃO/SENÃO) para que o valor de um campo seja gerado com base no valor de outro campo na mesma linha.
- **Constraints de Unicidade:** Garanta a unicidade de uma ou mais colunas combinadas (chave única composta) para refletir regras de negócio.
- **Tipos de Dados Variados:** Suporte nativo para `integer`, `float`, `string`, `boolean`, `datetime`, `uuid`, `lista de opções`, `regex` e um gerador de **nomes de pessoas** (em português).
- **Controle de Repetição e Ordenação:** Defina quantas vezes um valor pode se repetir e adicione múltiplas regras de ordenação para os dados de saída.
- **Configurações de Saída:** Escolha o caractere **separador** (vírgula, ponto e vírgula, etc.) e a **codificação** do arquivo (UTF-8, latin-1, etc.) para máxima compatibilidade.
- **Gerenciamento de Sessão:** Salve e carregue toda a sua configuração de múltiplos arquivos em um único arquivo `.json`, permitindo reutilizar layouts de dados complexos.

## Estrutura do Projeto

O projeto segue uma arquitetura em camadas para facilitar a manutenção e extensibilidade:

- **`main.py`**: Ponto de entrada da aplicação.
- **`ui/`**: Pacote contendo todos os módulos da interface gráfica.
  - `main_window.py`: A janela principal da aplicação (container).
  - `file_tab.py`: O componente que define uma única aba e toda a sua complexidade.
- **`data_generator.py`**: Camada de lógica, responsável por todo o processamento e geração de dados.
- **`utils.py`**: Módulo com classes auxiliares (como `Tooltip`) e constantes (listas de nomes).

## Pré-requisitos

- Python 3.10+
- Biblioteca `exrex`

## Instalação

1. Clone ou baixe este repositório.
2. Instale a dependência necessária:
   ```bash
   pip install exrex
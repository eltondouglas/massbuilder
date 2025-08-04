
---

### 2. `MANUAL_DE_UTILIZACAO.md`

```markdown
# 📘 Manual de Utilização - MassBuilder

Bem-vindo ao MassBuilder! Esta ferramenta foi projetada para simplificar a criação de massas de dados, desde as mais simples até as mais complexas com regras de negócio e relacionamentos.

## 🚀 Começando

A interface é dividida em três áreas principais:
1.  **Painel de Controle Global (Topo):** Onde você gerencia a sessão inteira (todos os arquivos), adiciona/remove arquivos e salva/carrega seu trabalho.
2.  **Painel de Abas (Centro):** A área principal. Cada aba representa um arquivo CSV a ser gerado, com suas próprias colunas e regras.
3.  **Botão de Geração (Base):** O botão "Gerar Todos os Arquivos" que inicia o processo.

## ⚙️ Guia Passo a Passo

### 1. Configurando seu Primeiro Arquivo

- **Nome do Arquivo:** Na primeira aba, no campo "Nome do Arquivo CSV", digite o nome desejado (ex: `clientes`). O título da aba será atualizado.
- **Linhas:** Defina a quantidade de registros a serem gerados.
- **Separador e Codificação:** Para garantir a compatibilidade com o Excel em português, é recomendado usar o separador **Ponto e Vírgula (;)** e a codificação **latin-1** ou **windows-1252**.

### 2. Adicionando e Configurando Campos (Colunas)

Dentro de cada aba de arquivo, há um painel de "Definição dos Campos".

- **Adicionar Campo:** Clique no botão para adicionar uma nova linha de configuração de campo.
- **Configurando um Campo:**
  - **Nome:** O nome da coluna no CSV.
  - **Tipo:** O tipo de dado a ser gerado. Opções incluem:
    - `integer`, `float`, `string`, `boolean`, `datetime`, `uuid`.
    - `lista_opcoes`: Gera valores a partir de uma lista que você fornece (ex: `Ativo, Inativo, Pendente`).
    - `regex`: Gera texto que segue um padrão de Expressão Regular.
    - `nome_pessoa`: Gera nomes completos realistas em português.
    - `chave_estrangeira`: Cria um relacionamento com outro arquivo (veja abaixo).
  - **Repetir:** Define quantas vezes cada valor gerado se repete. `1` significa que os valores serão únicos. `0` significa repetição aleatória.
- **Reordenar e Remover:** Use os botões `↑`, `↓` e `Remover` para organizar a ordem das colunas ou excluir um campo.

### 3. 🔗 Criando Dados Relacionais (Avançado)

Este é o recurso mais poderoso da ferramenta. Vamos criar um exemplo de `Clientes` e `Pedidos`.

#### a. Definindo a Chave Primária (PK)

1.  Na aba `clientes`, adicione um campo `ID_Cliente` do tipo `integer`.
2.  Marque a caixa de seleção **"É Chave Primária (PK)"**. Isso automaticamente força o campo a ter valores únicos.

#### b. Criando o Segundo Arquivo e a Chave Estrangeira (FK)

1.  No painel de controle global, clique em **"Adicionar Arquivo"**. Uma nova aba aparecerá.
2.  Renomeie a nova aba para `pedidos`.
3.  Adicione um campo `ID_Pedido` e marque-o como PK.
4.  Adicione um segundo campo chamado `Cliente_ID`. Para este campo:
    - Selecione o tipo **`chave_estrangeira`**.
    - Novos parâmetros aparecerão. Em **"Relação"**:
      - No primeiro dropdown, selecione o arquivo de origem: `clientes`.
      - No segundo dropdown, selecione o campo de origem: `ID_Cliente`.

#### c. Definindo a Cardinalidade

- Após definir a FK, um dropdown de **"Cardinalidade"** aparece.
  - **Um-para-Muitos (1:N):** (Padrão) Deixe esta opção para o nosso exemplo. Significa que um cliente pode ter muitos pedidos.
  - **Um-para-Um (1:1):** Use esta opção se a relação for única. Exemplo: um funcionário para um crachá. A ferramenta irá validar se o número de linhas do arquivo filho não é maior que o do pai.

### 4. 🧠 Aplicando Regras de Negócio (Avançado)

#### a. Geração Condicional (SE/ENTÃO/SENÃO)

Vamos garantir que apenas `Pessoas Jurídicas` (PJ) tenham `Inscrição Estadual` (IE).

1.  Crie um campo `TipoPessoa` (lista de opções: `PF,PJ`).
2.  Crie um campo `InscricaoEstadual` (tipo `string` ou `regex`).
3.  **Importante:** O campo `InscricaoEstadual` deve estar **abaixo** do campo `TipoPessoa` na lista.
4.  No campo `InscricaoEstadual`, clique em **"Adicionar Condição"**. Uma nova janela abrirá.
5.  Configure a regra:
    - **SE** o campo `TipoPessoa` **for igual a** `PJ`
    - **ENTÃO** `Usar Geração Padrão do Campo` (para gerar o número da IE).
    - **SENÃO** `Gerar com tipo` **Nulo/Vazio** (ou `Valor Fixo` com um texto como "N/A").
6.  Salve a regra. O botão "Adicionar Condição" ficará destacado, indicando que uma regra está ativa.

#### b. Constraints de Unicidade (Chave Composta)

Imagine que em um arquivo `itens_pedido`, a combinação de `ID_Pedido` e `ID_Produto` deve ser única.

1.  Na aba `itens_pedido`, vá para a aba interna **"Unicidade (Constraints)"**.
2.  Uma lista com todos os campos (`ID_Pedido`, `ID_Produto`, etc.) aparecerá.
3.  Segure `Ctrl` e clique em `ID_Pedido` e `ID_Produto` para selecionar ambos.
4.  Pronto! A ferramenta agora garantirá que nenhum par `(ID_Pedido, ID_Produto)` se repita.

### 5. Gerenciando sua Sessão

- **Salvar Sessão:** Salva a configuração de **todas as abas** em um único arquivo `.json`.
- **Carregar Sessão:** Restaura uma sessão salva anteriormente, recriando todas as abas e suas configurações.

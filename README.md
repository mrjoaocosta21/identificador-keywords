# Identificador Automático de Palavras-Chave

Trabalho da disciplina de Inteligência Artificial do bacharelado em Engenharia da Computação. O objetivo é desenvolver um sistema capaz de identificar automaticamente as palavras-chave mais relevantes de um texto utilizando métricas estatísticas de relevância.

A aplicação foi escrita em Python, com interface Streamlit e processamento de linguagem natural com NLTK. A primeira métrica implementada é a **frequência absoluta de grupos de termos com o mesmo radical**. Não há treinamento de modelo.

## Requisitos da disciplina

O programa deve:

1. Ler um texto ou conjunto de documentos.
2. Realizar pré-processamento:
   - Converter para minúsculas.
   - Remover acentos.
   - Remover pontuações.
   - Remover stopwords.
   - Aplicar stemming.
3. Calcular a frequência de cada termo.
4. Exibir as N palavras-chave mais relevantes com sua respectiva frequência.

## Executar

É necessário Python 3.11 ou superior. Na pasta do projeto:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Abra o endereço local informado pelo Streamlit, normalmente `http://localhost:8501`.

A instalação das dependências precisa de acesso à internet. Depois dela, a análise funciona sem rede: a lista de stopwords acompanha o projeto e o stemmer escolhido não exige download de corpus durante o uso.

As dependências diretas estão fixadas em `requirements.txt`: Streamlit 1.67.0 e NLTK 3.10.4. Para desenvolvimento, `requirements-dev.txt` acrescenta pytest 9.2.0 e Ruff 0.17.6.

## Usar a aplicação

1. Escolha entre colar um texto e enviar arquivos `.txt`.
2. Informe quantos resultados deseja ver, por meio do campo N.
3. Solicite a análise.
4. Consulte o ranking consolidado ou selecione um documento.
5. Explore as etapas de pré-processamento e, se desejar, exporte o ranking exibido em CSV.

O botão **Usar texto de exemplo** carrega um texto pronto; **Limpar análise** descarta o texto e os resultados da sessão. Alterações na entrada ou em N são aplicadas ao pressionar **Analisar conteúdo** novamente.

A tabela apresenta o termo representativo, o radical usado no agrupamento, a frequência agregada e as variantes encontradas. O termo representativo é a forma original em minúsculas mais frequente naquele grupo; em caso de empate, prevalece a ordem alfabética.

O ranking usa frequência decrescente e desempate alfabético pelo termo representativo. N limita apenas a quantidade de linhas exibidas: as métricas continuam considerando todos os termos processados. Se houver menos de N grupos, todos são apresentados.

As métricas diferenciam palavras identificadas antes da filtragem, ocorrências mantidas após a remoção de stopwords e grupos distintos após o stemming. Em vários documentos, a frequência consolidada soma as ocorrências de todos eles; os rankings individuais preservam o contexto de cada arquivo.

O gráfico opcional compara até 15 grupos. A tabela e o CSV contêm todas as linhas do ranking selecionado, até o N solicitado. As etapas mostram prévias de até 4.000 caracteres ou 200 termos para facilitar a leitura; esses recortes não limitam a contagem do documento completo.

### Entradas e limites

- Texto colado ou arquivos `.txt` codificados em UTF-8, com ou sem BOM.
- Até 20 documentos por análise.
- Até 1.000.000 bytes por arquivo enviado.
- Até 2.000.000 de caracteres no conjunto de textos.
- N deve ser um número inteiro positivo.
- Arquivos vazios, conteúdo binário e codificações incompatíveis geram mensagens de erro.
- Um texto composto apenas de stopwords ou pontuação gera um resultado vazio, sem inventar palavras-chave.

Somente sequências de letras são tratadas como palavras; números e símbolos funcionam como separadores. Por exemplo, `5G` produz o token `g`. Não há um comprimento mínimo arbitrário para as palavras: siglas curtas também podem participar da análise. PDF e DOCX não são aceitos nesta versão.

O CSV usa separador `;` e UTF-8 com BOM para facilitar a abertura em planilhas e contém os campos do ranking selecionado. Os documentos enviados são processados em memória; a aplicação não os grava em disco. Em execução local, o processamento ocorre no processo Python da máquina que iniciou o Streamlit. Ao hospedar a aplicação em outro computador, o processamento passa a ocorrer nesse servidor.

## Como o processamento funciona

```text
Texto ou documentos
        ↓
Minúsculas e separação das palavras
        ↓
Normalização para comparação e remoção de stopwords
        ↓
Stemming em português
        ↓
Agrupamento, contagem e ordenação
        ↓
Seleção dos N resultados
```

Pontuação é tratada como separador: `dados,textos` se torna duas palavras, e não `dadostextos`. A normalização de acentos é aplicada também às stopwords para que as comparações sejam consistentes.

A lista local contém 203 stopwords do projeto Snowball. A origem e a data da cópia estão registradas em [palavras_chave/data/README.md](palavras_chave/data/README.md). O NLTK fornece o stemmer usado pela aplicação; sua lista de stopwords não precisa ser baixada.

### Acentos e stemming

O algoritmo Snowball para português possui regras que dependem de letras e sufixos acentuados. Por isso, cada palavra mantém uma forma em minúsculas com acentos para o stemming e uma forma sem acentos para comparação com as stopwords. O radical de saída é normalizado sem acentos para o agrupamento.

Todas as operações solicitadas no enunciado são realizadas, mas elas não formam uma única sequência destrutiva na ordem em que foram listadas. A preservação da forma acentuada evita descartar informação antes de aplicar as regras do stemmer. Se a avaliação exigir literalmente remover os acentos antes do stemming, essa decisão precisa ser ajustada e os resultados comparados novamente. A [definição do algoritmo português](https://snowballstem.org/algorithms/portuguese/stemmer.html) documenta as regras acentuadas.

Stemming reduz palavras a radicais e não equivale à lematização. Os radicais podem ser incompletos, palavras relacionadas podem permanecer separadas e palavras de sentidos diferentes podem acabar no mesmo grupo. A coluna de variantes ajuda a inspecionar esses casos. Palavras escritas sem acentos podem produzir resultados diferentes das formas acentuadas.

### O que a frequência representa

A frequência é a contagem das ocorrências que compartilham um radical. Ela serve como um critério estatístico inicial de relevância, sem garantir que os primeiros termos sejam os melhores descritores do assunto. A qualidade também depende do texto, da lista de stopwords e dos agrupamentos produzidos pelo stemmer.

TF-IDF pode ser uma evolução para considerar a distribuição dos termos em uma coleção de documentos. Ele não está implementado nesta versão e não substituiria a frequência exigida pelo trabalho.

## Organização do código

```text
app.py                         Interface Streamlit
palavras_chave/
    models.py                  Documentos e resultados estruturados
    inputs.py                  Leitura e validação das entradas
    processing.py              Normalização, stopwords e stemming
    analysis.py                Orquestração, contagem e ranking
    export.py                  Exportação do ranking
    data/stopwords_pt.txt       Lista local de stopwords
tests/                         Testes do núcleo, entradas, interface e CSV
exemplos/                      Textos para demonstração
```

O núcleo não depende da interface. O pré-processador admite substituição de stopwords e da função de stemming, o que permite testar as regras de contagem isoladamente e experimentar outras estratégias sem alterar a tela. A aplicação não precisa de banco de dados nem de uma API separada.

## Validação e desenvolvimento

Com o ambiente virtual ativado:

```sh
python -m pip install -r requirements-dev.txt
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

Os testes cobrem contagem e agrupamento, ordenação e empates, consolidação de documentos, acentos, stopwords, pontuação sem espaços, entradas vazias e os limites de N e dos arquivos. Os testes da interface usam o AppTest do Streamlit com uploads reais, seleção de documentos, etapas do processamento, limpeza e tratamento de erros. A exportação é verificada pela leitura do CSV, incluindo acentos, separador e frequências.

O AppTest não substitui a verificação visual nem a avaliação com tecnologias assistivas. A navegação por teclado, o foco, os rótulos e a leitura em telas pequenas também devem ser conferidos no navegador ao modificar a interface.

### Roteiro de demonstração

1. Envie `exemplos/pln.txt` e selecione um N pequeno.
2. Explique a diferença entre palavra representativa, radical e frequência do grupo.
3. Abra as etapas para mostrar o que muda após a normalização, a filtragem e o stemming.
4. Acrescente `exemplos/educacao.txt` e compare o ranking consolidado com os individuais.
5. Analise `a e o de para` para demonstrar o estado sem termos restantes.
6. Exporte um ranking e confira as mesmas linhas no arquivo CSV.

O resultado esperado da demonstração é tornar o processamento verificável; não é necessário afirmar que o sistema compreende o significado do texto.

## Referências

- [NLTK: processamento de português e stopwords](https://www.nltk.org/howto/portuguese_en.html).
- [NLTK: Snowball e stemmer português](https://www.nltk.org/api/nltk.stem.snowball.html).
- [Snowball: algoritmo de stemming para português](https://snowballstem.org/algorithms/portuguese/stemmer.html).
- [Snowball: lista de stopwords em português](https://snowballstem.org/algorithms/portuguese/stop.txt).
- [Streamlit: documentação](https://docs.streamlit.io/).

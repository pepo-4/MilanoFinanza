# MilanoFinanza · Hackathon

Analisi di notizie e quotazioni Milano Finanza su BigQuery (progetto `class-hackaton-12`).

## Setup

### 1. Autenticazione Google Cloud

Serve la [gcloud CLI](https://cloud.google.com/sdk/docs/install). Poi:

```bash
gcloud auth login                                  # login utente per la CLI (bq, gcloud)
gcloud auth application-default login              # credenziali usate dalle librerie Python
gcloud config set project class-hackaton-12
```

Opzionale, per togliere l'avviso "without a quota project":

```bash
gcloud auth application-default set-quota-project class-hackaton-12
```

Verifica:

```bash
bq ls --project_id=class-hackaton-12               # deve mostrare i dataset news e financial_instruments
```

### 2. Ambiente Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Se su Ubuntu/Debian `python3 -m venv` fallisce per `ensurepip`, installa `python3-venv` (`sudo apt install python3-venv`) oppure usa [uv](https://docs.astral.sh/uv/):

```bash
uv venv .venv --seed
uv pip install --python .venv/bin/python -r requirements.txt
```

### 3. nbstripout (obbligatorio)

Gli output dei notebook contengono testo delle notizie, che non deve finire nei commit. Dopo ogni clone:

```bash
.venv/bin/nbstripout --install --attributes .gitattributes
.venv/bin/nbstripout --status                      # deve dire "nbstripout is installed"
```

### 4. Kernel Jupyter

```bash
.venv/bin/python -m ipykernel install --user --name mf-hackathon --display-name "Python (MF hackathon)"
jupyter lab                                        # oppure apri i notebook da VS Code scegliendo .venv
```

Primo test: esegui `notebooks/00_test_bigquery.ipynb` dall'inizio alla fine. Deve stampare dataset, schemi e l'ultima notizia.

## Branch di lavoro

Ognuno lavora sul proprio branch; `main` si aggiorna solo tramite merge/pull request.

| Persona | Branch |
|---|---|
| Giuseppe Allocca | `giuseppe-allocca` |
| Matteo Bottari | `matteo-bottari` |
| Edoardo Coli | `edoardo-coli` |
| Jacopo Ferrante | `jacopo-ferrante` |
| Giuseppe Leogrande | `giuseppe-leogrande` |

### Primo accesso

```bash
git clone https://github.com/pepo-4/MilanoFinanza.git
cd MilanoFinanza

# identità git solo per questa repo (usa i tuoi dati)
git config user.name "Nome Cognome"
git config user.email "tua@email.it"

# passa al tuo branch (es. matteo-bottari)
git switch matteo-bottari
```

Poi completa il [Setup](#setup) (venv, nbstripout, kernel).

### Lavoro quotidiano

```bash
git switch <tuo-branch>                  # assicurati di essere sul tuo branch
git branch --show-current                # verifica

git pull                                 # prendi le ultime modifiche del tuo branch
git merge origin/main                    # (opzionale) porta nel tuo branch le novità di main

git add <file>
git commit -m "descrizione"
git push                                 # il branch è già collegato a origin/<tuo-branch>
```

Se `git switch <tuo-branch>` dice che il branch non esiste, aggiorna prima l'elenco dei branch remoti con `git fetch origin`.

## Regole d'uso di BigQuery

La quota è limitata e si pagano i **byte letti** (`LIMIT` non riduce il costo). Le regole complete sono in [CLAUDE.md](CLAUDE.md); in breve:

- leggi lo schema prima di scrivere query (gratuito);
- mai `SELECT *`;
- filtra sempre sulla colonna di partizione (`news.articles.data_modifica`, `instruments_quotes.DATA_QUOTAZ`);
- dry run prima di ogni query; oltre 1 GB serve conferma (le funzioni `dry_run` / `run_query` del notebook 00 lo fanno già).

## Dati e riservatezza

Non committare credenziali, `.env` o dati estratti: sono contenuti protetti di Milano Finanza. Salva i dati locali in `data/`, che è esclusa da git.

# 🚁 Validar Medição - QGIS Plugin

**Versão:** 1.4.1 | **QGIS Mínimo:** 3.40.3
**Categoria:** Vector / Web / Raster Processing

Plugin desenvolvido para otimizar a validação de bacias de captação e terraços executados pela CODEVASF, utilizando produtos de aerolevantamentos com drones (DJI Mavic 3 Enterprise, etc).

A versão 1.4.0 transforma o plugin em uma esteira completa de processamento, introduzindo um conversor nativo de imagens COG (Cloud Optimized GeoTIFF) e um motor **WMS Local** (MapServer) integrado. Processe e renderize gigabytes de Ortofotos e Modelos Digitais de Elevação instantaneamente.

---

## ✨ Principais Funcionalidades

### ⚙️ 1. Pipeline de Otimização COG (Novo!)
* **Fim da dependência de softwares externos:** Otimize arquivos TIF brutos de dezenas de gigabytes diretamente pelo QGIS.
* **Processamento Seguro em Segundo Plano (Threads):** Barras de progresso duplas (por lote e por arquivo) mantêm você informado sem travar a interface do QGIS. Botão de interrupção de emergência incluído.
* **Inteligência de Compressão:** Aplica automaticamente compressão JPEG (85%) para Ortofotos (foco no desempenho) e compressão Deflate (Lossless) para MDT/MDS, preservando a precisão altimétrica milimétrica.
* **Organização Automática:** Lê a data de modificação dos voos e organiza os arquivos otimizados em pastas estruturadas (ex: `2025-JUNHO`).

### 🚀 2. Motor WMS Independente (MapServer)
* **Mosaicos Virtuais (VRT) Automáticos:** Varre diretórios, detecta arquivos COG e constrói mosaicos de forma inteligente.
* **Renderização de Terreno Nativa:** Detecta automaticamente Modelos Digitais de Elevação e aplica algoritmos de renderização instantânea (`SCALE=AUTO`).
* **Consulta de Elevação via Clique (GetFeatureInfo):** Use a ferramenta "Informações de Feições" do QGIS para clicar em qualquer ponto do MDT/MDS renderizado e obter a altitude exata (ou valores RGB nas ortofotos).
* **Injeção Dinâmica na Legenda:** As camadas são carregadas e organizadas automaticamente em grupos (pastas) na legenda do QGIS (ex: `[+] Ortofotos 2025`), prevenindo duplicidade.

### 📐 3. Ferramentas Vetoriais para Fiscalização
* Ferramentas exclusivas de desenho vetorial para geração automática de Bacias de Captação (12m, 24m ou raios customizados) e Terraços.

---

## 🛠️ Como Usar o Fluxo de Aerolevantamentos

1. **Importar e Otimizar:** Clique no ícone de "Importação" na barra de ferramentas. Aponte a pasta com os arquivos TIF brutos do drone, escolha o tipo de produto e deixe o plugin gerar os arquivos COG na pasta do servidor.
2. **Configuração Inicial:** No ícone da Engrenagem ⚙️, aponte os diretórios raiz de cada produto.
3. **Iniciar o Servidor:** Clique no ícone de Play ▶️. O motor WMS irá iniciar na porta `8080` e agrupar seus mosaicos automaticamente. Selecione as camadas desejadas para adicioná-las ao painel.
4. **Fiscalizar:** Utilize a ferramenta de Informações (i) nativa do QGIS sobre a camada de MDT para extrair cotas de elevação instantaneamente.

---

## 👨‍💻 Autor

**Givaldo Cavalcanti** *CODEVASF - Companhia de Desenvolvimento dos Vales do São Francisco e do Parnaíba*
[givaldo.junior@codevasf.gov.br](mailto:givaldo.junior@codevasf.gov.br)

---
*Desenvolvido em Python / PyQt5 para o ambiente QGIS.*
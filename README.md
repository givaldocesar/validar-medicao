# Validar Medição - QGIS Plugin

**Versão:** 1.3.1 | **QGIS Mínimo:** 3.40
**Categoria:** Vector / Web

Plugin desenvolvido para otimizar a validação das bacias de captação e terraços executados pela CODEVASF, utilizando produtos de aerolevantamentos com drones. 

A partir da versão 1.3.0, o plugin introduz um **Servidor WMS Local** integrado (MapServer), projetado para processar e renderizar gigabytes de Ortofotos e Modelos Digitais de Elevação instantaneamente, sem sobrecarregar a memória do QGIS.

---

## Principais Funcionalidades (Módulo MapServer)

* **Motor WMS Independente:** O servidor roda em uma *thread* separada em segundo plano. O QGIS não trava durante o carregamento de imagens pesadas.
* **Mosaicos Virtuais (VRT) Automáticos:** Varre diretórios na rede ou discos locais, detecta arquivos raster (`.tif`, `.ecw`) e constrói mosaicos de forma inteligente, organizados por ano e mês, caso os diretórios tenham essa informação no nome.
* **Suporte Nativo a MDT/MDS:** Caso encontre imagens no diretórios selecionados para Modelos Digitais de Terreno e Superfície, aplica algoritmos de renderização (`SCALE=AUTO`), transformando dados de elevação em imagens visíveis instantaneamente.
* **Configuração Persistente:** Utiliza a memória do próprio QGIS para salvar os caminhos de rede. Configure uma vez e a ferramenta nunca mais esquecerá.
* **Injeção Dinâmica na Legenda:** Interface gráfica elegante para seleção das camadas, que são carregadas e organizadas automaticamente em grupos (pastas) na legenda do QGIS, prevenindo duplicidade de arquivos.

*(O plugin também possui ferramentas exclusivas de desenho vetorial para geração automática de Bacias de Captação e Terraços, voltadas para fiscalização de obras).*

---

A interface foi projetada para ser simples e "Plug and Play". Na barra de ferramentas do plugin, você encontrará os ícones de controle.

### 1. Configuração Inicial (Engrenagem ⚙️)
Antes de ligar o servidor pela primeira vez, clique no ícone de Configurações.
* Na aba **Diretórios de Imagens**, aponte as pastas raízes onde seus produtos estão armazenados (Ortofotos, MDT, MDS, Curvas de Nível). 
* *Nota: O plugin ignora pastas deixadas em branco.*
* Clique em **Salvar Configurações**.

### 2. Iniciar o Servidor (Mapa 🗺️)
Clique no ícone de Mapa na barra de ferramentas. O plugin irá:
1. Verificar se já possui os arquivos do mapserver e bibliotecas python para utilização do servidor.
2. Se não tiver, fará os downloads necessários.
3. Rastrear todos os arquivos raster nas pastas configuradas.
4. Agrupar os meses detectados.
5. Ligar o motor MapServer local.
6. Abrir uma janela para você selecionar quais meses deseja adicionar ao painel de camadas.

### 3. Gerenciamento do Servidor
Dentro da aba de Configurações (Avançado), você tem total controle sobre o ciclo de vida do motor WMS, podendo **Iniciar**, **Parar (Stop)** a porta de rede ou **Reiniciar (Reboot)** o servidor em caso de inclusão de novas imagens nas pastas enquanto o QGIS estiver aberto.

---

## ⚠️ Limitações Conhecidas & Dicas
* **Arquivos Suportados (WMS):** Atualmente, a varredura do motor WMS procura especificamente por rasters com extensão `.tif` e `.ecw`.
* **Desempenho:** Recomendamos manter os arquivos pesados em um servidor robusto ou SSD local para maior fluidez do motor WMS.
* **Segurança de Thread:** Nunca feche o terminal do MapServer à força. Utilize o botão nativo de "Stop" ou "Reboot" no painel de configurações para que o plugin libere a porta 8080 do Windows com segurança.

---

## 👨‍💻 Autor

**Givaldo Cavalcanti** *CODEVASF - Companhia de Desenvolvimento dos Vales do São Francisco e do Parnaíba*
[givaldo.junior@codevasf.gov.br](mailto:givaldo.junior@codevasf.gov.br)

---
*Desenvolvido em Python / PyQt5 para o ambiente QGIS.*
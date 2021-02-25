#!/bin/sh


#### Requisites ________________________________________________________________
pip3 install libhxl
pip3 install hug

# If you plan to use ngrok to proxy for external world, use something like
sudo snap install ngrok

#### The tests _________________________________________________________________

### hxl2example ----------------------------------------------------------------

hxl2example tests/files/iris_hxlated-csv.csv | head
hxl2example tests/files/iris_hxlated-csv.csv temp/iris.tab
hxl2example https://docs.google.com/spreadsheets/u/1/d/1l7POf1WPfzgJb-ks4JM86akFSvaZOhAUWqafSJsm3Y4/edit#gid=634938833 | head
hxl2example https://docs.google.com/spreadsheets/u/1/d/1l7POf1WPfzgJb-ks4JM86akFSvaZOhAUWqafSJsm3Y4/edit#gid=634938833 data-mining-projects/output/HXL-CPLP-Exemplar_iris.tab

## hug -f bin/hxl2example ......................................................
#@see https://hugapi.github.io/hug/
#@see https://github.com/hugapi/hug/
hug -f bin/hxl2example

curl --silent http://localhost:8000/hxl2example.csv?source_url=https://docs.google.com/spreadsheets/u/1/d/1l7POf1WPfzgJb-ks4JM86akFSvaZOhAUWqafSJsm3Y4/edit#gid=634938833 | head
# HXLStandard_HXLCoreSchema_CoreHashtags
curl --silent http://localhost:8000/hxl2example.csv?source_url=https://docs.google.com/spreadsheets/d/1En9FlmM8PrbTWgl3UHPF_MXnJ6ziVZFhBbojSJzBdLI/edit#gid=319251406 | head

### hxl2tab --------------------------------------------------------------------

hxl2tab tests/files/iris_hxlated-csv.csv temp/iris.tab
hxl2tab https://docs.google.com/spreadsheets/d/1vFkBSharAEg5g5K2u_iDLCBvpWWPqpzC1hcL6QpFNZY/edit#gid=245471857 data-mining-projects/output/hxl2tab-spec.tab
hxl2tab https://docs.google.com/spreadsheets/u/1/d/1l7POf1WPfzgJb-ks4JM86akFSvaZOhAUWqafSJsm3Y4/edit#gid=634938833 data-mining-projects/output/HXL-CPLP-Exemplar_iris.tab
hxl2tab https://docs.google.com/spreadsheets/d/1sYqhbAcwLe7hnwAJk7Qljlq-YH31DZT3GNVqPIBykV4/edit#gid=1357271284 data-mining-projects/output/HXL-CPLP-Exemplar_golf-weather_nominal.tab

hxl2tab https://docs.google.com/spreadsheets/d/1Vqv6-EAdSHMSZvZtE426aXkDiwP8Mdrpft3tiGQ1RH0/edit#gid=0 temp/example-ebola-dataset-1_HXLated+tab.tab
hxl2tab https://docs.google.com/spreadsheets/d/1Vqv6-EAdSHMSZvZtE426aXkDiwP8Mdrpft3tiGQ1RH0/edit#gid=0 temp/example-ebola-dataset-1_HXLated+tab_hxltabv15.tab
hxl2tab https://docs.google.com/spreadsheets/d/1Vqv6-EAdSHMSZvZtE426aXkDiwP8Mdrpft3tiGQ1RH0/edit#gid=0 temp/example-ebola-dataset-1_HXLated+tab_hxltabv15_b.tab
hxl2tab https://docs.google.com/spreadsheets/d/1Vqv6-EAdSHMSZvZtE426aXkDiwP8Mdrpft3tiGQ1RH0/edit#gid=0 temp/example-ebola-dataset-1_HXLated+tab_hxltabv16.tab

## hug -f bin/hxl2tab ..........................................................
#@see https://hugapi.github.io/hug/
#@see https://github.com/hugapi/hug/
hug -f bin/hxl2tab

# See something like
#    - http://localhost:8000/hxl2tab.tab?source_url=https://docs.google.com/spreadsheets/u/1/d/1l7POf1WPfzgJb-ks4JM86akFSvaZOhAUWqafSJsm3Y4/edit#gid=634938833

# This will allow use hxl2tab via http. With ngrok could be used to quick allow
# others to use your computer as quick interface

### hxlquickmeta ---------------------------------------------------------------
hxlquickmeta --hxlquickmeta-hashtag="#adm2+code" --hxlquickmeta-value="BR3106200"

hxlquickmeta tests/files/iris_hxlated-csv.csv
hxlquickmeta https://docs.google.com/spreadsheets/u/1/d/1l7POf1WPfzgJb-ks4JM86akFSvaZOhAUWqafSJsm3Y4/edit#gid=634938833
hxlquickmeta https://docs.google.com/spreadsheets/u/1/d/1l7POf1WPfzgJb-ks4JM86akFSvaZOhAUWqafSJsm3Y4/edit#gid=634938833
hxlquickmeta https://data.humdata.org/dataset/2d058968-9d7e-49a9-b28f-2895d7f6536f/resource/a12bad12-f5ea-493c-9faa-66cb3f3e9ca7/download/fts_incoming_funding_bra.csv

# Non HXLated CSV, use hxlquickimport
hxlquickimport tests/files/iris.csv | hxlquickmeta

# HXL-CPLP-Vocab_Bool; @see https://github.com/HXL-CPLP/forum/issues/49
hxlquickmeta https://docs.google.com/spreadsheets/d/1hGUxMN2ywWNv8ONQ59Pp9Q4nG-eTRnAs0SyWunFZUDg/edit#gid=214068544

## hug -f bin/hxlquickmeta ......................................................
#@see https://hugapi.github.io/hug/
#@see https://github.com/hugapi/hug/
hug -f bin/hxlquickmeta

curl --silent http://localhost:8000/hxlquickmeta.csv?source_url=https://docs.google.com/spreadsheets/u/1/d/1l7POf1WPfzgJb-ks4JM86akFSvaZOhAUWqafSJsm3Y4/edit#gid=634938833 | head
# HXLStandard_HXLCoreSchema_CoreHashtags
curl --silent http://localhost:8000/hxlquickmeta.csv?source_url=https://docs.google.com/spreadsheets/d/1En9FlmM8PrbTWgl3UHPF_MXnJ6ziVZFhBbojSJzBdLI/edit#gid=319251406 | head


### hxlquickimport -------------------------------------------------------------

hxlquickimport hxlquickimport_samples/covid19mexico_10itens.csv
hxlquickimport hxlquickimport_samples/covid19mexico_10itens.csv temp/covid19mexico_10itens.hxl.csv

# With this command, an non-HXLated dataset can be converted directly to hxl2tab
# (including poorly non human reviewed tags)
hxlquickimport hxlquickimport_samples/covid19mexico_10itens.csv | hxl2tab

hxlquickimport https://drive.google.com/file/d/1nQAu6lHvdh2AV7q6aewGBQIxFz7VrCF9/view?usp=sharing | hxl2tab > temp/mx.gob.dados_dataset_informacion-referente-a-casos-covid-19-en-mexico_2020-06-01.hxl.csv
hxlquickimport https://docs.google.com/spreadsheets/d/1GQVrCQGEetx7RmKaZJ8eD5dgsr5i1zNy_UJpX3_AgrE/edit#gid=1715408033 > 'temp/hxlquickimport(v1.0)+hxl2tab(v1.4)__br.einstein_dataset_covid-pacientes-hospital-albert-einstein-anonimizado_2020-03-28.hxl.tab'
hxlquickimport https://docs.google.com/spreadsheets/d/1GQVrCQGEetx7RmKaZJ8eD5dgsr5i1zNy_UJpX3_AgrE/edit#gid=1715408033 | hxl2tab > 'temp/hxlquickimport(v1.0)+hxl2tab(v1.4)__br.einstein_dataset_covid-pacientes-hospital-albert-einstein-anonimizado_2020-03-28.hxl.tab'

hxlselect tests/files/iris_hxlated-csv+meta.hxl

### hxlquickimporttab ----------------------------------------------------------

hxlquickimporttab tests/files/iris_hxlated-tab.tab temp/iris_hxlated-csv-from-tab.csv
hxlquickimporttab tests/files/iris_hxlated-tab.tab temp/iris_hxlated-csv-from-tab.csv | head
hxl2tab https://docs.google.com/spreadsheets/d/1Vqv6-EAdSHMSZvZtE426aXkDiwP8Mdrpft3tiGQ1RH0/edit#gid=0 | head

hxlquickimporttab temp/titanic.tab | head


### hxl2encryption -------------------------------------------------------------
hxl2encryption tests/files/iris_hxlated-csv.csv | head
### hxl2decryption -------------------------------------------------------------
hxl2decryption tests/files/iris_hxlated-csv.csv | head

#### [meta issue] HXL and data directly from and to SQL databases #10 __________
# @see https://docs.sqlalchemy.org/en/13/dialects/
# @see https://github.com/wireservice/csvkit/blob/master/csvkit/utilities/csvsql.py

# TODO: Create an local PostgreSQL database
# @see https://csvkit.readthedocs.io/en/latest/scripts/csvsql.html
# createdb hxltest

# Generate create schema
csvsql tests/files/iris_hxlated-csv.csv --dialect postgresql --skip-lines 1
csvsql tests/files/iris_hxlated-csv.csv --dialect mysql --skip-lines 1
# CREATE TABLE "iris_hxlated-csv" (
# 	"#item+eng_sepal+eng_length+number" DECIMAL NOT NULL, 
# 	"#item+eng_sepal+eng_width+number" DECIMAL NOT NULL, 
# 	"#item+eng_petal+eng_length+number" DECIMAL NOT NULL, 
# 	"#item+eng_petal+eng_width+number" DECIMAL NOT NULL, 
# 	"#item+class+vt_class" VARCHAR NOT NULL
# );
csvsql tests/files/iris_hxlated-csv.csv --dialect mysql --skip-lines 1
# CREATE TABLE `iris_hxlated-csv` (
# 	`#item+eng_sepal+eng_length+number` DECIMAL(38, 1) NOT NULL, 
# 	`#item+eng_sepal+eng_width+number` DECIMAL(38, 1) NOT NULL, 
# 	`#item+eng_petal+eng_length+number` DECIMAL(38, 1) NOT NULL, 
# 	`#item+eng_petal+eng_width+number` DECIMAL(38, 1) NOT NULL, 
# 	`#item+class+vt_class` VARCHAR(15) NOT NULL
# );
csvsql tests/files/iris_hxlated-csv.csv --dialect sqlite --skip-lines 1
# CREATE TABLE "iris_hxlated-csv" (
# 	"#item+eng_sepal+eng_length+number" FLOAT NOT NULL, 
# 	"#item+eng_sepal+eng_width+number" FLOAT NOT NULL, 
# 	"#item+eng_petal+eng_length+number" FLOAT NOT NULL, 
# 	"#item+eng_petal+eng_width+number" FLOAT NOT NULL, 
# 	"#item+class+vt_class" VARCHAR NOT NULL
# );
csvsql tests/files/iris_hxlated-csv.csv --dialect mssql --skip-lines 1
# CREATE TABLE [iris_hxlated-csv] (
# 	[#item+eng_sepal+eng_length+number] DECIMAL(38, 1) NOT NULL, 
# 	[#item+eng_sepal+eng_width+number] DECIMAL(38, 1) NOT NULL, 
# 	[#item+eng_petal+eng_length+number] DECIMAL(38, 1) NOT NULL, 
# 	[#item+eng_petal+eng_width+number] DECIMAL(38, 1) NOT NULL, 
# 	[#item+class+vt_class] VARCHAR(max) NOT NULL
# );

# Insert data directly on the server
csvsql tests/files/iris_hxlated-csv.csv --db 'postgresql://postgres:password@localhost/hxltest' --skip-lines 1

#### Build hxlmeta local storage _______________________________________________
# @see https://github.com/EticaAI/HXL-Data-Science-file-formats/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc
# Note: these hxlmeta examples may not actually be used by the HXLMeta Class
#       but could at least be used to test importing/exporting from databases

# @see https://github.com/harelba/q/blob/master/test/BENCHMARK.md

# TODO hxl2example --remove-headers example.com/dataset hxlmeta-data/HXLMeta_DataType.hxl.csv

### HXLMeta_DataType, HXLMeta_StorageType, HXLMeta_StatisticalType
hxl2example https://docs.google.com/spreadsheets/d/1hGUxMN2ywWNv8ONQ59Pp9Q4nG-eTRnAs0SyWunFZUDg/edit#gid=214068544 hxlmeta-data/HXLMeta_DataType.hxl.csv
hxl2example https://docs.google.com/spreadsheets/d/1vFkBSharAEg5g5K2u_iDLCBvpWWPqpzC1hcL6QpFNZY/edit#gid=211012023 hxlmeta-data/HXLMeta_StorageType.hxl.csv
hxl2example https://docs.google.com/spreadsheets/d/1vFkBSharAEg5g5K2u_iDLCBvpWWPqpzC1hcL6QpFNZY/edit#gid=1566300457 hxlmeta-data/HXLMeta_StatisticalType.hxl.csv
hxl2example https://docs.google.com/spreadsheets/d/1vFkBSharAEg5g5K2u_iDLCBvpWWPqpzC1hcL6QpFNZY/edit#gid=1053765950 hxlmeta-data/HXLMeta_LevelType.hxl.csv
hxl2example https://docs.google.com/spreadsheets/d/1vFkBSharAEg5g5K2u_iDLCBvpWWPqpzC1hcL6QpFNZY/edit#gid=617579056 hxlmeta-data/HXLMeta_UsageType.hxl.csv

### HXL-CPLP-Vocab_Bool --------------------------------------------------------
# @see https://github.com/HXL-CPLP/forum/issues/49
hxl2example https://docs.google.com/spreadsheets/d/1hGUxMN2ywWNv8ONQ59Pp9Q4nG-eTRnAs0SyWunFZUDg/edit#gid=214068544 hxlmeta-data/HXL-CPLP-Vocab_Bool.hxl.csv

### UNOCHA-countries-territories -----------------------------------------------
# https://vocabulary.unocha.org/
hxl2example https://docs.google.com/spreadsheets/d/1NjSI2LaS3SqbgYc0HdD8oIb7lofGtiHgoKKATCpwVdY/edit#gid=1088874596 hxlmeta-data/UNOCHA_countries-territories.hxl.csv

### HXL-CPLP-FOD_languages -----------------------------------------------------
hxl2example https://docs.google.com/spreadsheets/d/12k4BWqq5c3mV9ihQscPIwtuDa_QRB-iFohO7dXSSptI/edit#gid=0 hxlmeta-data/HXL-CPLP-FOD_languages.hxl.csv

### HXLStandard_Data-types --------------------------------------------------
hxl2example https://docs.google.com/spreadsheets/d/1En9FlmM8PrbTWgl3UHPF_MXnJ6ziVZFhBbojSJzBdLI/edit#gid=1881622062 hxlmeta-data/HXLStandard_Data-types.hxl.csv

### HXLStandard_Core-hashtags --------------------------------------------------
hxl2example https://docs.google.com/spreadsheets/d/1En9FlmM8PrbTWgl3UHPF_MXnJ6ziVZFhBbojSJzBdLI/edit#gid=319251406 hxlmeta-data/HXLStandard_Core-hashtags.hxl.csv

### HXLStandard_Core-attributes ------------------------------------------------
hxl2example https://docs.google.com/spreadsheets/d/1En9FlmM8PrbTWgl3UHPF_MXnJ6ziVZFhBbojSJzBdLI/edit#gid=1810309357 hxlmeta-data/HXLStandard_Core-attributes.hxl.csv

#### Ignore after this part ___________________________________________________
# fititnt@bravo:/workspace/data/brasil_inep_microdados-enem-2019/DADOS$ head -n 1000 MICRODADOS_ENEM_2019.csv > MICRODADOS_ENEM_2019_head-n-1000.csv
hxlquickimport hxlquickimport_samples/MICRODADOS_ENEM_2019_head-n-1000.csv | hxl2tab

head -n 3 hxlquickimport_samples/MICRODADOS_ENEM_2019_head-n-1000_quick-utf8-bom.csv | hxltag --map NU_INSCRICAO#item+incricao --default-tag='#item' 
head -n 3 hxlquickimport_samples/MICRODADOS_ENEM_2019_head-n-1000_quick-utf8.csv | hxltag --map NU_INSCRICAO#item+incricao --default-tag='#item' 
head -n 3 hxlquickimport_samples/MICRODADOS_ENEM_2019_head-n-1000.csv | hxltag --map NU_INSCRICAO#item+incricao --default-tag='#item' 


#### Rocha's local development notes _________________________________________
# VSCode python code suggestion is wonderful, but have some issues with
# namespaced packages when doing local development. So this trick is how Rocha
# do: a bunch of symlinks

mv /home/fititnt/.local/lib/python3.8/site-packages/hxlm /home/fititnt/.local/lib/python3.8/site-packages/hxlm-old
ln -s /workspace/git/EticaAI/HXL-Data-Science-file-formats/hxlm  /home/fititnt/.local/lib/python3.8/site-packages/hxlm
ln -s /workspace/git/EticaAI/hxlm-crypto-eticaai/hxlm/crypto /workspace/git/EticaAI/HXL-Data-Science-file-formats/hxlm/crypto
ln -s /workspace/git/EticaAI/hxlm-crypto-eticaai/hxlm/plugin/xe_cryptoexample /workspace/git/EticaAI/HXL-Data-Science-file-formats/hxlm/plugin/xe_cryptoexample

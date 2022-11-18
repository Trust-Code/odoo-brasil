


# Adicionar num pre-migracao
Deixa instalar o l10n_br_account_enterprise pq modificou o nome da coluna
ALTER TABLE public.account_fiscal_position_tax_rule_prod_fiscal_clas_relation RENAME COLUMN product_fiscal_classification_id TO account_ncm_id;


# Seta a empresa na linha dos documento eletronicos
update eletronic_document_line edl set company_id = (select company_id from eletronic_document ed where edl.eletronic_document_id = ed.id)

# Atualiza as linhas com a chave para o documento eltronico
update eletronic_document_line set eletronic_document_id = invoice_eletronic_id 

# Atualiza o documento eletronico com a fatura correta
update eletronic_document ed set move_id = (select move_id from account_invoice ai where ai.id = ed.invoice_id)

# Atualiza o campo de ncm que modificou
update product_template set l10n_br_ncm_id  = fiscal_classification_id;
update product_template set l10n_br_origin = origin;
update product_template set l10n_br_fiscal_category_id = fiscal_category_id;
update product_template pt set service_code = (select codigo_servico_paulistana from account_service_type ast where pt.service_type_id = ast.id)


# Atualiza o codigo ibge da cidade
update res_city set l10n_br_ibge_code = ibge_code;

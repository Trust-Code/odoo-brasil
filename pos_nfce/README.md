# POS NFC-e
> Esse modulo permite o usuario do odoo emitir NFC-e via POS ou Invoice

[![NPM Version][npm-image]][npm-url]
[![Build Status][travis-image]][travis-url]
[![Downloads Stats][npm-downloads]][npm-url]

Esse modulo permite o usuario do odoo emitir NFC-e via POS ou Invoice, ultilizando as configurações nativas do Odoo e extensões da Trust-Code

## Instalação
Para instalar esse modulo não é necessario muita coisa, é só coloca o mesmo na pasta dos addons personalizada e atualizar a lista de aplicativos, depois pesquisa o nome do modulo.

## Configuração
Para fazer a configuração do modulo siga os passos abaixo:
* Para fazer a configuração do modulo primeiro precisa ir em configurações
Nessa parte você precisa Configurar os Dados da sua Empresa, em Informações Gerais, principalmente o dados do certificado, ID do CSC e CSC.
Depois em Dados Fiscais você precisa adicionar o regime da sua empresa.
Pronto essa étapa ja foi, var para proxima.

* Inventario -> Configurações -> Faturamento
Nessa étapa você precisa adicionar um plano de contas e uma moeda.
> Observação, as vezes a moeda troca para USD ao troca o plano de contas e salvar, se a atente nisso.
Pronto essa étapa ja foi, var para proxima.

* Faturamento -> Configuração -> Contabilidade -> Posições fiscais
Nessa étapa é necessario criar uma posição fiscal e isso envolve parte de tributação ao qual não posso dizer como configurar, mas irei dizer os principais pontos para ser informado.
Detectar Automaticamente: Deixa marcado;
Tipo da posição: Saída;
País: Brasil;
Finalidade: Normal;
Consumidor final: Sim;
Tipo de operação: Presencial.
Outras Informações:
    Documento Produto: Nota Fiscal de Consumidor Eletrônica – NFC-e;
Pronto essa étapa ja foi, var para proxima.

* Ponto de Venda -> Configurações -> Ponto de Venda -> Caixa
Nessa parte é só preencher algumas coisas e fazer isso para todos os caixa que você precisar
Posição Fiscal (Use a default specific tax regime): Posiçao que você acabou de criar
Faturamento: Marca e escolha pra onde o sistema deva contabilizar.
Finalmente agora é só emitir a NFC-e.

## Contribuição

1. Fork it (<https://github.com/Trust-Code/odoo-brasil/fork>)
2. Crie uma branch para sua modificação (`git checkout -b feature/fooBar`)
3. Faça o commit (`git commit -am 'Add some fooBar'`)
4. Push para o branch (`git push origin feature/fooBar`)
5. Crie um novo Pull Request

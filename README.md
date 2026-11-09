# Slack Explorer

Gerenciador de arquivos gráfico para Slackware Linux, inspirado na organização do
Explorador de Arquivos do Windows e construído apenas com Python 3 e Tkinter.

## Recursos da versão 0.1

- navegação pela pasta pessoal e por todo o sistema de arquivos (`/`);
- voltar, avançar, subir um nível, início e barra de endereço;
- pesquisa instantânea dentro da pasta atual;
- lista com tipo, tamanho, data de modificação e permissões Linux;
- exibição opcional de arquivos ocultos (`Ctrl+H`);
- abertura de arquivos com o aplicativo padrão do Slackware;
- atalhos para Documentos, Downloads, Imagens, Música, Vídeos e mídias removíveis;
- nenhuma função de exclusão, recorte ou alteração de arquivos nesta versão.

O aplicativo exibe tudo que o usuário atual tem permissão para ler. Pastas
administrativas protegidas continuam respeitando as permissões do Linux.

## Executar

```bash
python3 run.py
```

## Testes

```bash
python3 -m unittest discover -v
```

## Requisitos

- Slackware 15.0 ou mais recente;
- Python 3 com Tkinter 8.6;
- `xdg-open` para abrir arquivos com seus aplicativos padrão.

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import re
from urllib.parse import urlparse

def criar_diretorio_data():
    """Cria o diretório 'data' se não existir"""
    if not os.path.exists('data'):
        os.makedirs('data')
        print("Diretório 'data' criado com sucesso.")
    else:
        print("Diretório 'data' já existe.")

def realizar_login(usuario, senha):
    """Realiza login"""
    options = webdriver.ChromeOptions()
    options.add_argument('--enable-cookies')
    options.add_argument('handle-all-redirects=true')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument('--headless')
    
    # Adicionar configurações para download automático
    prefs = {
        "download.default_directory": os.path.abspath("data"),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)
    
    # Inicializar o driver
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    except Exception as e:
        print(f"Erro ao inicializar o Chrome: {str(e)}")
        return None
    
    try:
        # Acessar a página de login
        driver.get('https://ead.unibalsas.edu.br/login/index.php')
        
        # Aguardar até que o campo de usuário esteja presente
        usuario_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        
        # Encontrar os elementos e preencher os campos
        usuario_input.send_keys(usuario)
        
        senha_input = driver.find_element(By.ID, "password")
        senha_input.send_keys(senha)
        
        # Clicar no botão de login
        botao_login = driver.find_element(By.ID, "loginbtn")
        botao_login.click()
        
        # Aguardar o redirecionamento
        WebDriverWait(driver, 10).until(
            EC.url_changes('https://ead.unibalsas.edu.br/login/index.php')
        )
        
        print("Login realizado com sucesso!")
        return driver
        
    except Exception as e:
        print(f"Erro ao realizar login: {str(e)}")
        driver.quit()
        return None

def navegar_e_extrair_cursos(driver):
    """Extrai a lista de cursos disponíveis"""
    try:
        # Aguardar até que os elementos da página estejam carregados
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "mc_content_list"))
        )
        
        # Encontrar todos os elementos de curso
        cursos = driver.find_elements(By.CSS_SELECTOR, '[data-region="course-content"]')
        
        dados_cursos = []
        
        for curso in cursos:
            try:
                # Extrair o ID do curso
                curso_id = curso.get_attribute('data-course-id')
                
                # Encontrar o link de visualização
                link_view = curso.find_element(By.CSS_SELECTOR, 'a.mcc_view')
                url_curso = link_view.get_attribute('href')
                
                # Extrair o nome do curso
                try:
                    nome_curso = curso.find_element(By.CSS_SELECTOR, '.coursename').text
                except:
                    nome_curso = f"Curso-{curso_id}"
                
                dados_curso = {
                    'id': curso_id,
                    'nome': nome_curso,
                    'url': url_curso
                }
                
                dados_cursos.append(dados_curso)
                
            except Exception as e:
                print(f"Erro ao processar curso: {str(e)}")
                continue
        
        return dados_cursos
        
    except Exception as e:
        print(f"Erro ao navegar e extrair dados: {str(e)}")
        return None

def baixar_arquivo_com_selenium(driver, url, nome_arquivo, pasta_destino='data'):
    """Baixa um arquivo diretamente usando o navegador Selenium"""
    try:
        # Armazenar a janela atual
        janela_atual = driver.current_window_handle
        
        # Abrir nova aba
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        
        # Navegar para a URL do arquivo
        driver.get(url)
        time.sleep(2)  # Aguarda o carregamento
        
        # Se for URL de pluginfile.php (link direto do Moodle), baixa diretamente
        if 'pluginfile.php' in url:
            print(f"    √ Baixando arquivo diretamente: {url}")
            time.sleep(3)
            print(f"    √ Download iniciado, verificando na pasta {pasta_destino}")
            driver.close()
            driver.switch_to.window(janela_atual)
            return True
        
        # Verificar se estamos olhando para o PDF incorporado ou um frame
        frames = driver.find_elements(By.TAG_NAME, 'iframe')
        download_links = driver.find_elements(By.PARTIAL_LINK_TEXT, 'Download')
        
        pdf_url = url
        if frames:
            try:
                frame_src = frames[0].get_attribute('src')
                if frame_src and '.pdf' in frame_src:
                    pdf_url = frame_src
                    print(f"    √ Encontrado PDF em iframe: {pdf_url}")
                    driver.get(pdf_url)
                    time.sleep(2)
            except Exception as e:
                print(f"    ! Aviso ao processar frame: {str(e)}")
        elif download_links:
            try:
                pdf_url = download_links[0].get_attribute('href')
                print(f"    √ Encontrado link de download: {pdf_url}")
                driver.get(pdf_url)
                time.sleep(2)
            except Exception as e:
                print(f"    ! Aviso ao processar link de download: {str(e)}")
        
        # Verificar se a página atual contém um PDF incorporado
        current_url = driver.current_url
        if '.pdf' in current_url.lower():
            print(f"    √ URL direta para PDF detectada: {current_url}")
            time.sleep(3) 
            driver.close()
            driver.switch_to.window(janela_atual)
            return True
        
        # Buscar um objeto ou embed com PDF
        pdf_objects = driver.find_elements(By.XPATH, "//object[contains(@data, '.pdf')] | //embed[contains(@src, '.pdf')]")
        if pdf_objects:
            for obj in pdf_objects:
                try:
                    pdf_url = obj.get_attribute('data') or obj.get_attribute('src')
                    if pdf_url:
                        print(f"    √ Encontrado PDF em objeto: {pdf_url}")
                        driver.get(pdf_url)
                        time.sleep(3)
                        break
                except:
                    continue
        
        # Fechar aba e voltar à original
        driver.close()
        driver.switch_to.window(janela_atual)
        
        print(f"    ⚠ O arquivo pode ter sido baixado para a pasta de downloads do navegador.")
        
        return True
    
    except Exception as e:
        print(f"    ✗ Erro ao baixar arquivo: {str(e)}")
        # Garantir que voltamos à janela original
        try:
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(janela_atual)
        except:
            pass
        return False

def acessar_e_baixar_pdfs_curso(driver, curso):
    """Acessa um curso e baixa todos os PDFs encontrados"""
    print(f"\n[+] Acessando curso: {curso['nome']} (ID: {curso['id']})")
    
    pasta_destino = 'data'
    
    # Configurar o diretório de download para a pasta data
    try:
        driver.execute_cdp_cmd('Page.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': os.path.abspath(pasta_destino)
        })
    except Exception as e:
        print(f"  ! Aviso: Não foi possível atualizar o diretório de download: {str(e)}")
    
    # Acessar a URL do curso
    driver.get(curso['url'])
    
    # Aguardar o carregamento da página
    time.sleep(2)
    
    # Encontrar todos os links na página
    links = driver.find_elements(By.TAG_NAME, 'a')
    
    # Filtrar links de PDFs
    pdf_links = []
    for link in links:
        try:
            href = link.get_attribute('href')
            if href and (href.endswith('.pdf') or '/mod/resource/view.php' in href):
                texto = link.text.strip() or f"arquivo_{len(pdf_links)+1}"
                # Evitar duplicatas
                if not any(pl['url'] == href for pl in pdf_links):
                    pdf_links.append({
                        'url': href,
                        'texto': texto
                    })
        except:
            continue
    
    print(f"  - Encontrados {len(pdf_links)} possíveis arquivos para download")
    
    # Acessar cada link e baixar o PDF
    pdfs_baixados = 0
    for idx, pdf in enumerate(pdf_links):
        try:
            # Criar um nome de arquivo seguro com prefixo do curso para evitar conflitos
            curso_prefixo = re.sub(r'[\\/*?:"<>|]', "_", curso['nome'])[:20]
            texto_arquivo = re.sub(r'[\\/*?:"<>|]', "_", pdf['texto'])
            nome_arquivo = f"{curso_prefixo}_{texto_arquivo[:30]}.pdf" if not texto_arquivo.endswith('.pdf') else f"{curso_prefixo}_{texto_arquivo[:34]}"
            
            print(f"  - Baixando: {nome_arquivo} [{idx+1}/{len(pdf_links)}]")
            
            # Usar o método modificado que usa o próprio navegador para baixar
            sucesso = baixar_arquivo_com_selenium(driver, pdf['url'], nome_arquivo, pasta_destino)
            
            if sucesso:
                pdfs_baixados += 1
                
        except Exception as e:
            print(f"    ✗ Erro ao baixar PDF: {str(e)}")
    
    print(f"  - PDFs baixados para este curso: {pdfs_baixados}")
    return pdfs_baixados

def buscar_recursos_adicionais(driver, curso):
    """Busca por recursos adicionais dentro do curso"""
    try:
        # Encontrar links para seções/módulos do curso
        secoes = driver.find_elements(By.CSS_SELECTOR, 'li.section')
        
        for secao in secoes:
            try:
                # Verificar se há botões para expandir conteúdo
                botoes_expandir = secao.find_elements(By.CSS_SELECTOR, 'button.expand-collapse')
                for botao in botoes_expandir:
                    try:
                        botao.click()
                        time.sleep(0.5) 
                    except:
                        pass
            except:
                pass
            botoes_collapse = secao.find_elements(By.CSS_SELECTOR, '.collapsed, [aria-expanded="false"]')
            for botao in botoes_collapse:
                try:
                    botao.click()
                    time.sleep(0.5)
                except:
                    pass
    except Exception as e:
        print(f"  - Aviso: Não foi possível expandir seções: {str(e)}")
        
    # Re-executar o download após expansão
    return acessar_e_baixar_pdfs_curso(driver, curso)

def encontrar_links_diretos_aos_pdfs(driver, curso):
    """Método alternativo para encontrar links diretos para PDFs no curso"""
    print(f"\n[+] Tentando método alternativo para curso: {curso['nome']}")
    
    # Acessar a URL do curso
    driver.get(curso['url'])
    time.sleep(2)
    
    pasta_destino = 'data'
    
    # Configurar o diretório de download para a pasta data
    try:
        driver.execute_cdp_cmd('Page.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': os.path.abspath(pasta_destino)
        })
    except Exception as e:
        print(f"  ! Aviso: Não foi possível atualizar o diretório de download: {str(e)}")
    
    pdfs_baixados = 0
    
    # Procurar por todos os recursos no curso
    recursos = driver.find_elements(By.CSS_SELECTOR, '.activityinstance, .activity')
    
    for recurso in recursos:
        try:
            # Encontrar o link
            link = recurso.find_element(By.TAG_NAME, 'a')
            href = link.get_attribute('href')
            
            # Verificar se é um link relevante
            if href and ('/mod/resource' in href or '/pluginfile.php' in href):
                texto = link.text.strip() or f"recurso_{len(recursos)+1}"
                print(f"  - Tentando acessar recurso: {texto}")
                curso_prefixo = re.sub(r'[\\/*?:"<>|]', "_", curso['nome'])[:20]
                texto_arquivo = re.sub(r'[\\/*?:"<>|]', "_", texto)
                nome_arquivo = f"{curso_prefixo}_{texto_arquivo[:30]}.pdf" if not texto_arquivo.endswith('.pdf') else f"{curso_prefixo}_{texto_arquivo[:34]}"
                
                # Baixar o arquivo
                sucesso = baixar_arquivo_com_selenium(driver, href, nome_arquivo, pasta_destino)
                
                if sucesso:
                    pdfs_baixados += 1
        except Exception as e:
            print(f"    ! Erro ao processar recurso: {str(e)}")
    
    print(f"  - PDFs baixados usando método alternativo: {pdfs_baixados}")
    return pdfs_baixados

def main():
    """Função principal para execução do script"""
    # Configurações
    usuario = ''
    senha = ''
    
    driver = None
    
    try:
        # Criar diretório para armazenar os PDFs
        criar_diretorio_data()
        
        # Iniciar processo de login
        driver = realizar_login(usuario, senha)
        
        if not driver:
            print("Não foi possível realizar o login. Encerrando.")
            return
        
        # Extrair lista de cursos
        cursos = navegar_e_extrair_cursos(driver)
        
        if not cursos:
            print("Não foram encontrados cursos. Verifique seu acesso.")
            return
        
        print(f"\nForam encontrados {len(cursos)} cursos.")
        
        # Contador de estatísticas
        total_pdfs = 0
        
        # Para cada curso, acessar e baixar PDFs
        for i, curso in enumerate(cursos):
            print(f"\nProcessando curso {i+1}/{len(cursos)}: {curso['nome']}")
            
            # Primeiro acesso e download inicial
            pdfs_baixados = acessar_e_baixar_pdfs_curso(driver, curso)
            
            # Buscar recursos adicionais que possam estar ocultos
            if pdfs_baixados == 0:
                print("  - Tentando localizar recursos adicionais...")
                pdfs_baixados = buscar_recursos_adicionais(driver, curso)
            
            # Se ainda não tiver PDFs, tentar método alternativo
            if pdfs_baixados == 0:
                print("  - Tentando método alternativo de busca...")
                pdfs_baixados = encontrar_links_diretos_aos_pdfs(driver, curso)
            
            total_pdfs += pdfs_baixados
        
        print(f"\n=== Resumo da Execução ===")
        print(f"Total de cursos processados: {len(cursos)}")
        print(f"Total de PDFs baixados: {total_pdfs}")
        print(f"PDFs salvos no diretório: './data/'")
        
    except KeyboardInterrupt:
        print("\nOperação interrompida pelo usuário.")
    except Exception as e:
        print(f"\nErro durante a execução: {str(e)}")
    
    finally:
        # Fechar o navegador com segurança
        if driver:
            try:
                print("\nEncerrando o navegador...")
                driver.quit()
                print("Navegador encerrado com sucesso.")
            except Exception as e:
                print(f"Erro ao fechar navegador: {str(e)}")

# Execução do script
if __name__ == "__main__":
    main()
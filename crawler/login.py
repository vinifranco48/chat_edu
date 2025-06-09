import time
import traceback
import os
import tempfile
import shutil
import atexit
from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,  # Exceções específicas primeiro
                                        TimeoutException)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
# --- Função de Login (com wait para senha) ---
_temp_dirs_to_cleanup = []

def _cleanup_temp_dirs():
    """Função para limpar diretórios temporários na saída do programa"""
    global _temp_dirs_to_cleanup
    for temp_dir in _temp_dirs_to_cleanup:
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"Diretório temporário limpo: {temp_dir}")
        except Exception as e:
            print(f"Erro ao limpar diretório {temp_dir}: {e}")

# Registra a função de limpeza para ser executada na saída do programa
atexit.register(_cleanup_temp_dirs)

def realizar_login(usuario, senha):
    """
    Realiza login no EAD Unibalsas de forma robusta para rodar em um servidor Docker.
    
    Retorna:
        webdriver.Chrome: Driver do Chrome em caso de sucesso
        None: Em caso de falha
    """
    global _temp_dirs_to_cleanup
    
    # --- CONFIGURAÇÃO DAS OPÇÕES DO CHROME PARA AMBIENTE DE SERVIDOR ---
    options = Options()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # CORREÇÃO 1: Modo Headless é essencial para rodar em servidor sem interface gráfica.
    options.add_argument("--headless=new")
    
    # Argumentos necessários para estabilidade em contêineres Docker.
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # CORREÇÃO 2: Cria um diretório de perfil temporário e único para cada sessão.
    # Isso evita o erro "user data directory is already in use".
    user_data_dir = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={user_data_dir}")
    
    # Adiciona o diretório à lista de limpeza automática
    _temp_dirs_to_cleanup.append(user_data_dir)

    driver = None
    try:
        print("🚀 Inicializando o WebDriver...")
        service = Service(ChromeDriverManager().install())
        
        print("   - Inicializando webdriver.Chrome...")
        driver = webdriver.Chrome(service=service, options=options)
        driver.maximize_window()
        print("✅ WebDriver inicializado com sucesso.")

    except Exception as e_init:
        print(f"❌ Erro Crítico: Não foi possível inicializar o Chrome/WebDriver: {str(e_init)}")
        traceback.print_exc()
        # Remove o diretório da lista e limpa imediatamente em caso de falha
        if user_data_dir in _temp_dirs_to_cleanup:
            _temp_dirs_to_cleanup.remove(user_data_dir)
        try:
            shutil.rmtree(user_data_dir)
        except:
            pass
        return None

    # --- LÓGICA DE LOGIN ---
    try:
        login_url = 'https://ead.unibalsas.edu.br/login/index.php'
        print(f"Acessando a página de login: {login_url}")
        driver.get(login_url)

        print("Aguardando campo de usuário (ID: username)...")
        usuario_input = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "username"))
        )
        usuario_input.clear()
        usuario_input.send_keys(usuario)
        print("   - Usuário inserido.")

        print("Aguardando campo de senha (ID: password)...")
        senha_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "password"))
        )
        senha_input.clear()
        senha_input.send_keys(senha)
        print("   - Senha inserida.")

        print("Aguardando botão de login (ID: loginbtn)...")
        botao_login = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "loginbtn"))
        )
        botao_login.click()
        print("   - Botão de login clicado.")

        print("Aguardando confirmação de login...")
        WebDriverWait(driver, 25).until(
            EC.any_of(
                EC.url_contains('/my/'),
                EC.presence_of_element_located((By.ID, "nav-drawer"))
            )
        )
        print("   - Confirmação de login detectada.")

        # Verificação final para garantir que não estamos na página de login
        if "login/index.php" in driver.current_url:
            print("   - ERRO DE LOGIN: Credenciais inválidas ou falha inesperada.")
            # Fecha o driver e limpa recursos
            driver.quit()
            return None

        print("Login realizado com sucesso!")
        
        # NOVO: Adiciona um atributo personalizado ao driver para rastrear seu diretório temp
        driver._temp_user_data_dir = user_data_dir
        
        return driver  # ✅ Retorna apenas o driver

    except Exception as e_login:
        print(f"❌ Erro inesperado durante o processo de login: {str(e_login)}")
        traceback.print_exc()
        if driver:
            try:
                driver.save_screenshot("erro_durante_login.png")
            except:
                pass
            driver.quit()
        return None

def fechar_driver_com_limpeza(driver):
    """
    Função auxiliar para fechar o driver e limpar o diretório temporário associado.
    """
    global _temp_dirs_to_cleanup
    
    if driver is None:
        return
    
    # Pega o diretório temporário se foi armazenado no driver
    temp_dir = getattr(driver, '_temp_user_data_dir', None)
    
    try:
        driver.quit()
        print("Driver fechado com sucesso.")
    except Exception as e:
        print(f"Erro ao fechar driver: {e}")
    
    # Limpa o diretório temporário imediatamente
    if temp_dir and temp_dir in _temp_dirs_to_cleanup:
        _temp_dirs_to_cleanup.remove(temp_dir)
        try:
            shutil.rmtree(temp_dir)
            print(f"Diretório temporário limpo: {temp_dir}")
        except Exception as e:
            print(f"Erro ao limpar diretório temporário {temp_dir}: {e}")


# --- Função para Coletar IDs/URLs e depois visitar cada página (Mantida como estava, já robusta) ---
def navegar_e_extrair_cursos_visitando(driver):
    """
    Coleta IDs/URLs do painel, depois visita cada página de curso
    para extrair o nome real.
    """
    # (O resto do código permanece igual)
    cursos_a_visitar = []
    dados_cursos_final = []

    # --- FASE 1: Coletar IDs e URLs do Painel ---
    print("\n--- FASE 1: Coletando IDs e URLs do Painel ---")
    try:
        dashboard_url = 'https://ead.unibalsas.edu.br/my/'
        if "/my/" not in driver.current_url:
            print(f"Navegando para o painel: {dashboard_url}")
            driver.get(dashboard_url)
            # Esperar o painel carregar minimamente após navegar
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
            )
        else:
            print("Já está no painel ou URL similar.")

        # Espera a área de cursos carregar
        print("Aguardando a lista de cursos carregar no painel...")
        seletor_area_cursos = '[data-region="course-overview"], [data-region="myoverview"], [data-region*="course-list"], #region-main-box'
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, seletor_area_cursos))
            )
            print("   - Área de cursos encontrada no painel.")
            time.sleep(2) # Tempo extra para renderizar JS dinâmico, se houver
        except TimeoutException:
            print("   - Alerta: Área principal de cursos não encontrada com seletores padrão. Tentando encontrar links individuais...")


        # Encontra os elementos individuais dos cursos no painel
        seletores_curso_individual = [
            '.card.dashboard-card[data-course-id]', # Selector comum Moodle moderno
            'div.coursebox[data-courseid]',      # Selector comum Moodle clássico
            'li[data-courseid]',                 # Pode aparecer em listas
            'div[data-course-id]',               # Outro genérico
            '[data-region="course-content"]'     # Outra região possível
        ]
        cursos_elements = []
        print("Procurando elementos de curso com seletores:")
        for sel in seletores_curso_individual:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, sel)
                if elements:
                    print(f"   - Encontrados {len(elements)} elementos com '{sel}'")
                    cursos_elements.extend(elements) # Adiciona todos os encontrados
            except Exception as e_find:
                print(f"   - Erro buscando elementos com seletor '{sel}': {e_find}")

        # Remove duplicados baseado no elemento em si (mais seguro que só pelo ID depois)
        unique_elements = []
        seen_elements = set()
        for el in cursos_elements:
            # Usar o ID do WebElement é uma forma de identificar unicidade
            # Cuidado se a página recarregar elementos dinamicamente (pouco provável aqui)
            if el.id not in seen_elements:
                 unique_elements.append(el)
                 seen_elements.add(el.id)
        cursos_elements = unique_elements
        print(f"Total de elementos de curso únicos (baseado em WebElement ID): {len(cursos_elements)}")


        if not cursos_elements:
             # Fallback se nenhum bloco foi encontrado: procurar links diretos
             print("   - Nenhum bloco de curso encontrado pelos seletores principais, procurando links diretos 'view.php?id=...'")
             try:
                  # Procura links que ESTÃO dentro da área principal (evita pegar links do menu, etc.)
                  area_principal = driver.find_element(By.CSS_SELECTOR, "#region-main, [role='main']") # Ajuste se necessário
                  cursos_elements = area_principal.find_elements(By.CSS_SELECTOR, 'a[href*="course/view.php?id="]')
                  print(f"   - Encontrados {len(cursos_elements)} links diretos dentro da área principal.")
             except NoSuchElementException:
                  print("   - Área principal não encontrada para limitar busca de links diretos. Procurando em toda a página...")
                  try:
                      cursos_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="course/view.php?id="]')
                      print(f"   - Encontrados {len(cursos_elements)} links diretos na página inteira (pode incluir menus).")
                  except Exception as e_link_find_all:
                      print(f"   - Erro ao buscar links diretos na página inteira: {e_link_find_all}")
             except Exception as e_link_find:
                  print(f"   - Erro ao buscar links diretos: {e_link_find}")


        if not cursos_elements:
            print("ERRO FASE 1: Nenhum elemento ou link de curso encontrado no painel.")
            try:
                driver.save_screenshot("painel_sem_cursos_fase1.png")
                print("   - Screenshot 'painel_sem_cursos_fase1.png' salvo.")
            except: pass
            return [] # Retorna lista vazia em vez de None para consistência

        # Extrai ID e URL de cada elemento encontrado
        ids_coletados = set() # Para evitar duplicados pelo ID do curso
        print("Processando elementos encontrados para extrair ID e URL:")
        for i, element in enumerate(cursos_elements):
            curso_id = None
            url_curso = None
            nome_curso_painel = "Nome não encontrado no painel" # Nome preliminar

            # Tenta extrair ID do atributo 'data-course-id' ou 'data-courseid'
            curso_id = element.get_attribute('data-course-id') or element.get_attribute('data-courseid')

            # Tenta encontrar o link e extrair URL e ID dele
            link_tag = None
            try:
                # Se o próprio elemento for um link 'a' relevante
                if element.tag_name == 'a' and 'course/view.php?id=' in element.get_attribute('href'):
                     link_tag = element
                else:
                    # Procura um link 'a' relevante DENTRO do elemento
                    # Busca links que sejam descendentes diretos ou indiretos
                    possible_links = element.find_elements(By.CSS_SELECTOR, 'a[href*="course/view.php?id="]')
                    if possible_links:
                         link_tag = possible_links[0] # Pega o primeiro encontrado dentro do bloco

                if link_tag:
                    href = link_tag.get_attribute('href')
                    if href and 'id=' in href:
                        url_curso = href
                        # Extrai ID da URL como fallback ou confirmação
                        try:
                            id_from_url = href.split('id=')[1].split('&')[0]
                            if id_from_url.isdigit(): # Garante que é um número
                                if not curso_id:
                                    curso_id = id_from_url
                                elif curso_id != id_from_url:
                                    print(f"   - Aviso no elemento {i+1}: ID do atributo ({curso_id}) difere do ID da URL ({id_from_url}). Usando o da URL.")
                                    curso_id = id_from_url
                        except IndexError:
                             print(f"   - Aviso no elemento {i+1}: URL encontrada '{href}' mas não foi possível extrair o ID.")
                    # Tenta pegar um nome preliminar do link ou do bloco
                    try: nome_curso_painel = link_tag.text.strip() or element.text.strip()
                    except: pass

            except NoSuchElementException:
                # OK se não achar link interno, pode ser só um bloco com ID
                pass
            except Exception as e_link_extract:
                print(f"   - Erro ao processar link no elemento {i+1}: {e_link_extract}")

            # Se não conseguiu URL mas tem ID, constrói a URL padrão
            if not url_curso and curso_id:
                 url_curso = f'https://ead.unibalsas.edu.br/course/view.php?id={curso_id}'
                 print(f"   - URL construída para ID {curso_id} pois link não foi encontrado/processado.")

            # Adiciona à lista se tiver ID e URL válidos e não for duplicado
            if curso_id and url_curso:
                if curso_id not in ids_coletados:
                    cursos_a_visitar.append({
                        'id': curso_id,
                        'url': url_curso,
                        'nome_painel': nome_curso_painel # Guarda nome preliminar
                        })
                    ids_coletados.add(curso_id)
                    print(f"   + Coletado: ID={curso_id}, URL={url_curso}, Nome Preliminar='{nome_curso_painel[:50]}...'")
                # else: print(f"   - Info: ID={curso_id} já coletado, pulando duplicado.") # Opcional
            else:
                print(f"   - Aviso: Não foi possível extrair ID e/ou URL completos do elemento {i+1}")
                # Opcional: Imprimir HTML do elemento com problema
                # try: print(f"     HTML: {element.get_attribute('outerHTML')[:200]}...")
                # except: pass

        if not cursos_a_visitar:
            print("ERRO FASE 1: Nenhum ID/URL de curso válido foi coletado do painel.")
            return []

        print(f"--- FASE 1 Concluída: {len(cursos_a_visitar)} cursos únicos para visitar ---")

    except Exception as e_fase1:
        print(f"Erro Crítico na Fase 1 (Coleta no Painel): {str(e_fase1)}")
        traceback.print_exc()
        return [] # Retorna lista vazia

    # --- FASE 2: Visitar cada URL e Extrair Nome ---
    print(f"\n--- FASE 2: Visitando {len(cursos_a_visitar)} páginas de curso para buscar nomes ---")
    for i, curso_info in enumerate(cursos_a_visitar):
        print(f"\nProcessando curso {i+1}/{len(cursos_a_visitar)} (ID: {curso_info['id']})...")
        nome_final = f"ERRO_NomeNaoEncontrado (ID: {curso_info['id']})" # Default em caso de falha
        try:
            print(f"   - Navegando para: {curso_info['url']}")
            driver.get(curso_info['url'])

            # Espera pelo elemento do título na página do curso
            # Usar múltiplos seletores como fallback pode ser útil aqui também
            # Tenta primeiro o h4, depois h1, depois um título geral
            seletor_titulo_curso = 'h4.breadcrumb_title, h1' # Adicionado h1 como alternativa
            print(f"   - Aguardando título com seletores: '{seletor_titulo_curso}'")

            titulo_element = WebDriverWait(driver, 20).until(
                 EC.visibility_of_element_located((By.CSS_SELECTOR, seletor_titulo_curso))
            )

            nome_final = titulo_element.text.strip()
            print(f"   - >> Nome encontrado na página: '{nome_final}'")

        except TimeoutException:
            print(f"   - ❌ ERRO (Timeout): Não foi possível encontrar o título ('{seletor_titulo_curso}') na página do curso ID {curso_info['id']}.")
            print(f"   - URL visitada: {driver.current_url}")
            nome_final = f"ERRO_TimeoutBuscandoNome (ID: {curso_info['id']})"
            try: driver.save_screenshot(f"erro_timeout_curso_{curso_info['id']}.png")
            except: pass
        except NoSuchElementException:
            # Esta exceção não deveria ocorrer com WebDriverWait(visibility), mas por segurança
            print(f"   - ❌ ERRO (NoSuchElement): Elemento do título ('{seletor_titulo_curso}') não encontrado após espera na página do curso ID {curso_info['id']}.")
            nome_final = f"ERRO_ElementoNomeNaoEncontrado (ID: {curso_info['id']})"
            try: driver.save_screenshot(f"erro_nome_nao_encontrado_curso_{curso_info['id']}.png")
            except: pass
        except Exception as e_fase2_curso:
            print(f"   - ❌ ERRO Inesperado ao processar curso ID {curso_info['id']}: {str(e_fase2_curso)}")
            traceback.print_exc()
            nome_final = f"ERRO_INESPERADO_Processamento (ID: {curso_info['id']})"
            # Não salva screenshot para todo erro inesperado para não lotar

        # Adiciona os dados completos à lista final, usando nome_final
        dados_cursos_final.append({
            'id': curso_info['id'],
            'nome': nome_final,
            'url': curso_info['url']
        })
        # Pequena pausa opcional entre as visitas para não sobrecarregar o servidor
        # time.sleep(0.5)

    print(f"\n--- FASE 2 Concluída ---")
    return dados_cursos_final


# --- Função Principal (Usa a nova função de extração) ---
def main():
    """Função principal para execução do script"""
    # --- Configurações ---
    # Coloque suas credenciais aqui diretamente para teste
    # Ou use input() para pedir ao usuário (mais seguro)
    usuario = 'vinicius.franco@alu.unibalsas.edu.br' # SEU USUÁRIO AQUI
    senha = 'bem10048'                             # SUA SENHA AQUI
    # print("Por favor, informe suas credenciais do EAD Unibalsas:")
    # usuario = input("Digite seu usuário (email): ")
    # senha = input("Digite sua senha: ")

    driver = None # Inicializa a variável fora do try
    cursos_processados = [] # Inicializa lista de resultados
    start_time = time.time() # Medir tempo total

    try:
        # 1. Tenta realizar o login
        driver = realizar_login(usuario, senha)

        # 2. Verifica se o login foi bem-sucedido
        if not driver:
            print("\n-----------------------------------------")
            print("VALIDAÇÃO: Falha no login. Script encerrado.")
            print("-----------------------------------------")
            # Não precisa retornar aqui, o finally cuidará do tempo
        else:
            print("\n-----------------------------------------")
            print("VALIDAÇÃO: Login realizado com sucesso!")
            print(f"URL atual: {driver.current_url}")
            print("-----------------------------------------")

            # 3. Se o login funcionou, tenta extrair os cursos
            cursos_processados = navegar_e_extrair_cursos_visitando(driver)

            print("\n------------------- RESULTADO FINAL --------------------")
            if cursos_processados:
                print(f"MATÉRIAS PROCESSADAS ({len(cursos_processados)}):")
                erros_nome = 0
                for i, curso in enumerate(cursos_processados):
                    # Imprime formatado para melhor leitura
                    print(f"{i+1: >3}. ID: {curso.get('id', 'N/A'): <8} | Nome: {curso.get('nome', 'N/A')}")
                    # Descomente para ver a URL também
                    # print(f"      URL: {curso.get('url', 'N/A')}")
                    if "ERRO_" in curso.get('nome', ''):
                        erros_nome += 1
                if erros_nome > 0:
                    print(f"\nAlerta: {erros_nome} curso(s) tiveram erro na busca do nome na página do curso.")
                else:
                    print("\nTodos os nomes de curso foram extraídos com sucesso das páginas.")
            else:
                print("MATÉRIAS: Não foi possível listar ou processar as matérias após o login.")
            print("-------------------------------------------------------")

    except KeyboardInterrupt:
        # Permite interromper o script com Ctrl+C de forma limpa
        print("\nOperação interrompida pelo usuário (Ctrl+C).")
    except Exception as e_main:
        # Captura qualquer outra exceção não tratada
        print(f"\nErro inesperado durante a execução principal: {str(e_main)}")
        traceback.print_exc()
    finally:
        # Este bloco SEMPRE será executado, independentemente de erros ou interrupções
        end_time = time.time()
        print(f"\nTempo total de execução: {end_time - start_time:.2f} segundos")
        if driver:
            print("Encerrando o navegador...")
            try:
                driver.quit() # Garante que o navegador e o driver sejam fechados
                print("Navegador encerrado com sucesso.")
            except Exception as e_quit:
                print(f"Erro ao tentar fechar o navegador: {str(e_quit)}")
                print("Pode ser necessário fechar processos 'chrome' ou 'chromedriver' manualmente.")

# --- Execução do script ---
if __name__ == "__main__":
    main()
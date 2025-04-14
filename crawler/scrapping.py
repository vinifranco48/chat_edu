from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def realizar_login(usuario, senha):
    # Configurar o Chrome Driver
    options = webdriver.ChromeOptions()
    # Adicionar opção para aceitar cookies
    options.add_argument('--enable-cookies')
    
    # Inicializar o driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
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
        
        # Pegar o token de login (importante para a autenticação)
        login_token = driver.find_element(By.NAME, "logintoken").get_attribute("value")
        
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

def navegar_e_extrair_dados(driver):
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
                
                # Extrair outros detalhes do curso
                detalhes = curso.find_element(By.CLASS_NAME, 'details').text
                
                dados_curso = {
                    'id': curso_id,
                    'url': url_curso,
                    'detalhes': detalhes
                }
                
                dados_cursos.append(dados_curso)
                
                # Opcional: clicar no link (descomente se necessário)
                # link_view.click()
                # time.sleep(2)  # Aguardar carregamento da página
                # driver.back()  # Voltar para a página anterior
                
            except Exception as e:
                print(f"Erro ao processar curso: {str(e)}")
                continue
        
        return dados_cursos
        
    except Exception as e:
        print(f"Erro ao navegar e extrair dados: {str(e)}")
        return None

# Exemplo de uso
if __name__ == "__main__":
    usuario = ""
    senha = ""
    
    driver = realizar_login(usuario, senha)
    
    if driver:
        try:
            dados_cursos = navegar_e_extrair_dados(driver)
            
            if dados_cursos:
                print("\nDados extraídos dos cursos:")
                for curso in dados_cursos:
                    print(f"\nID do Curso: {curso['id']}")
                    print(f"URL: {curso['url']}")
                    print(f"Detalhes: {curso['detalhes']}")
            
        except Exception as e:
            print(f"Erro durante a execução: {str(e)}")
        
        finally:
            # Fechar o navegador
            driver.quit()
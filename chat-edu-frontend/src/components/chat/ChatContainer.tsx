import { useState } from 'react';
import { useCourse } from '@/contexts/CourseContext';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { api } from '@/services/api';
import { toast } from 'sonner';
import type { Message } from '@/types';
import { MessageSquare } from 'lucide-react';

export const ChatContainer = () => {
  const { selectedCourse } = useCourse();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (text: string) => {
    if (!selectedCourse) {
      toast.error('Selecione um curso primeiro');
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await api.sendChatMessage(text, selectedCourse.id);

      if (response.error) {
        throw new Error(response.error);
      }

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        text: response.response || 'Desculpe, não consegui processar sua pergunta.',
        sources: response.retrieved_sources,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Erro ao enviar mensagem';
      toast.error(errorMessage);
      console.error('Erro no chat:', error);
      
      // Adicionar mensagem de erro no chat
      const errorBotMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        text: `Desculpe, ocorreu um erro: ${errorMessage}. Por favor, tente novamente.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorBotMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!selectedCourse) {
    return (
      <div className="flex-1 flex items-center justify-center bg-muted/20">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-muted mx-auto flex items-center justify-center">
            <MessageSquare className="w-8 h-8 text-muted-foreground" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground">Nenhum curso selecionado</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Selecione um curso na barra lateral para começar a conversar
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      <div className="p-4 border-b bg-card">
        <h2 className="font-semibold text-foreground">{selectedCourse.nome}</h2>
        <p className="text-xs text-muted-foreground mt-1">
          Faça perguntas sobre o conteúdo do curso
        </p>
      </div>
      
      <MessageList messages={messages} isLoading={isLoading} />
      <MessageInput onSendMessage={sendMessage} isLoading={isLoading} />
    </div>
  );
};

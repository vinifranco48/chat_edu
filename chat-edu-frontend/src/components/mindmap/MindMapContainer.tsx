import { useState } from 'react';
import { useCourse } from '@/contexts/CourseContext';
import { Button } from '@/components/ui/button';
import { api } from '@/services/api';
import { toast } from 'sonner';
import type { MindMapData } from '@/types';
import { MindMapViewer } from './MindMapViewer';
import { Brain, Loader2 } from 'lucide-react';

export const MindMapContainer = () => {
  const { selectedCourse } = useCourse();
  const [mindMapData, setMindMapData] = useState<MindMapData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  console.log('MindMapContainer renderizado', { selectedCourse, mindMapData });

  const generateMindMap = async () => {
    if (!selectedCourse) {
      toast.error('Selecione um curso primeiro');
      return;
    }

    setIsLoading(true);
    try {
      console.log('Gerando mapa mental para curso:', selectedCourse.id, selectedCourse.nome);
      const data = await api.generateMindMap(selectedCourse.id, selectedCourse.nome);
      console.log('Mapa mental recebido:', data);
      
      if (!data || !data.nodes || !data.edges) {
        console.error('Dados do mapa mental inválidos:', data);
        throw new Error('Formato de resposta inválido');
      }
      
      setMindMapData(data);
      toast.success('Mapa mental gerado com sucesso!');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Erro ao gerar mapa mental';
      toast.error(errorMessage);
      console.error('Erro ao gerar mapa mental:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!selectedCourse) {
    return (
      <div className="flex-1 flex items-center justify-center bg-muted/20">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-muted mx-auto flex items-center justify-center">
            <Brain className="w-8 h-8 text-muted-foreground" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground">Nenhum curso selecionado</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Selecione um curso na barra lateral para gerar um mapa mental
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!mindMapData) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center space-y-6 max-w-md">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary/10 to-secondary/10 mx-auto flex items-center justify-center">
            <Brain className="w-10 h-10 text-primary" />
          </div>
          <div>
            <h3 className="text-xl font-semibold text-foreground">Gerar Mapa Mental</h3>
            <p className="text-sm text-muted-foreground mt-2">
              Crie um mapa mental visual do conteúdo do curso {selectedCourse.nome}
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              Este processo pode levar alguns segundos...
            </p>
          </div>
          <Button
            onClick={generateMindMap}
            disabled={isLoading}
            size="lg"
            className="bg-gradient-to-r from-primary to-secondary hover:opacity-90 transition-opacity"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Gerando...
              </>
            ) : (
              <>
                <Brain className="mr-2 h-5 w-5" />
                Gerar Mapa Mental
              </>
            )}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      <div className="p-4 border-b bg-card flex justify-between items-center">
        <div>
          <h2 className="font-semibold text-foreground">{selectedCourse.nome}</h2>
          <p className="text-xs text-muted-foreground mt-1">
            {mindMapData.nodes.length} conceitos mapeados
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setMindMapData(null)}
        >
          Gerar novo mapa
        </Button>
      </div>
      
      <MindMapViewer data={mindMapData} />
    </div>
  );
};

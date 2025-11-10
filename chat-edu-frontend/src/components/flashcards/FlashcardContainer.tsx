import { useState } from 'react';
import { useCourse } from '@/contexts/CourseContext';
import { Button } from '@/components/ui/button';
import { api } from '@/services/api';
import { toast } from 'sonner';
import type { Flashcard } from '@/types';
import { FlashcardCard } from './FlashcardCard';
import { Sparkles, BookOpen, Loader2 } from 'lucide-react';

export const FlashcardContainer = () => {
  const { selectedCourse } = useCourse();
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  console.log('FlashcardContainer renderizado', { selectedCourse, flashcards });

  const generateFlashcards = async () => {
    if (!selectedCourse) {
      toast.error('Selecione um curso primeiro');
      return;
    }

    setIsLoading(true);
    try {
      console.log('Gerando flashcards para curso:', selectedCourse.id);
      const cards = await api.generateFlashcards(selectedCourse.id);
      console.log('Flashcards recebidos:', cards);
      
      if (!Array.isArray(cards)) {
        console.error('Resposta não é um array:', cards);
        throw new Error('Formato de resposta inválido');
      }
      
      setFlashcards(cards);
      setCurrentIndex(0);
      toast.success(`${cards.length} flashcards gerados!`);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Erro ao gerar flashcards';
      toast.error(errorMessage);
      console.error('Erro ao gerar flashcards:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!selectedCourse) {
    return (
      <div className="flex-1 flex items-center justify-center bg-muted/20">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-muted mx-auto flex items-center justify-center">
            <BookOpen className="w-8 h-8 text-muted-foreground" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground">Nenhum curso selecionado</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Selecione um curso na barra lateral para gerar flashcards
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (flashcards.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center space-y-6 max-w-md">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary/10 to-secondary/10 mx-auto flex items-center justify-center">
            <Sparkles className="w-10 h-10 text-primary" />
          </div>
          <div>
            <h3 className="text-xl font-semibold text-foreground">Gerar Flashcards</h3>
            <p className="text-sm text-muted-foreground mt-2">
              Crie flashcards automaticamente a partir do conteúdo do curso {selectedCourse.nome}
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              Este processo pode levar alguns segundos...
            </p>
          </div>
          <Button
            onClick={generateFlashcards}
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
                <Sparkles className="mr-2 h-5 w-5" />
                Gerar Flashcards
              </>
            )}
          </Button>
        </div>
      </div>
    );
  }

  const handlePrevious = () => {
    setCurrentIndex((prev) => (prev > 0 ? prev - 1 : flashcards.length - 1));
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev < flashcards.length - 1 ? prev + 1 : 0));
  };

  return (
    <div className="flex-1 flex flex-col p-8">
      <div className="flex-1 flex items-center justify-center">
        <div className="w-full max-w-2xl space-y-6">
          <div className="text-center">
            <p className="text-sm text-muted-foreground">
              Card {currentIndex + 1} de {flashcards.length}
            </p>
          </div>

          <FlashcardCard flashcard={flashcards[currentIndex]} />

          <div className="flex justify-center gap-4">
            <Button variant="outline" onClick={handlePrevious}>
              Anterior
            </Button>
            <Button variant="outline" onClick={handleNext}>
              Próximo
            </Button>
          </div>

          <div className="text-center">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setFlashcards([]);
                setCurrentIndex(0);
              }}
            >
              Gerar novos flashcards
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

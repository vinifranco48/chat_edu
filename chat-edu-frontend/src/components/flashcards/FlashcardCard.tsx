import { useState } from 'react';
import { Card } from '@/components/ui/card';
import type { Flashcard } from '@/types';

interface FlashcardCardProps {
  flashcard: Flashcard;
}

export const FlashcardCard = ({ flashcard }: FlashcardCardProps) => {
  const [isFlipped, setIsFlipped] = useState(false);

  return (
    <div className="w-full">
      <Card 
        onClick={() => setIsFlipped(!isFlipped)}
        className="w-full h-[400px] cursor-pointer flex flex-col items-center justify-center p-8 hover:shadow-lg transition-shadow"
      >
        {!isFlipped ? (
          <div className="text-center space-y-4">
            {flashcard.category && (
              <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold mb-4 bg-secondary text-secondary-foreground">
                {flashcard.category}
              </div>
            )}
            <h3 className="text-2xl font-semibold text-foreground">
              {flashcard.question}
            </h3>
            <p className="text-sm text-muted-foreground mt-4">
              Clique para ver a resposta
            </p>
          </div>
        ) : (
          <div className="text-center space-y-4">
            <p className="text-lg text-foreground leading-relaxed">
              {flashcard.answer}
            </p>
            <p className="text-sm text-muted-foreground mt-4">
              Clique para voltar à pergunta
            </p>
          </div>
        )}
      </Card>
    </div>
  );
};

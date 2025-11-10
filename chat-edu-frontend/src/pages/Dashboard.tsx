import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ChatContainer } from '@/components/chat/ChatContainer';
import { FlashcardContainer } from '@/components/flashcards/FlashcardContainer';
import { MindMapContainer } from '@/components/mindmap/MindMapContainer';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { MessageSquare, Layers, Brain, Loader2 } from 'lucide-react';

const Dashboard = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, isLoading, navigate]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <Loader2 className="w-12 h-12 animate-spin text-primary mx-auto" />
          <p className="text-muted-foreground">Carregando dashboard...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="flex h-[calc(100vh-4rem)]">
        <Sidebar />
        <main className="flex-1 overflow-hidden">
          <Tabs defaultValue="chat" className="h-full flex flex-col">
            <div className="border-b bg-card px-4">
              <TabsList className="h-12">
                <TabsTrigger value="chat" className="gap-2">
                  <MessageSquare className="w-4 h-4" />
                  Chat
                </TabsTrigger>
                <TabsTrigger value="flashcards" className="gap-2">
                  <Layers className="w-4 h-4" />
                  Flashcards
                </TabsTrigger>
                <TabsTrigger value="mindmap" className="gap-2">
                  <Brain className="w-4 h-4" />
                  Mapa Mental
                </TabsTrigger>
              </TabsList>
            </div>
            
            <TabsContent value="chat" className="flex-1 m-0">
              <ErrorBoundary>
                <ChatContainer />
              </ErrorBoundary>
            </TabsContent>
            
            <TabsContent value="flashcards" className="flex-1 m-0">
              <ErrorBoundary>
                <div className="h-full">
                  <FlashcardContainer />
                </div>
              </ErrorBoundary>
            </TabsContent>
            
            <TabsContent value="mindmap" className="flex-1 m-0">
              <ErrorBoundary>
                <div className="h-full">
                  <MindMapContainer />
                </div>
              </ErrorBoundary>
            </TabsContent>
          </Tabs>
        </main>
      </div>
    </div>
  );
};

export default Dashboard;

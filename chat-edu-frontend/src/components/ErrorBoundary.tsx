import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: undefined });
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex-1 flex items-center justify-center p-8">
          <Card className="max-w-md p-6 space-y-4">
            <div className="flex items-center gap-3 text-destructive">
              <AlertCircle className="w-6 h-6" />
              <h3 className="text-lg font-semibold">Algo deu errado</h3>
            </div>
            <p className="text-sm text-muted-foreground">
              {this.state.error?.message || 'Ocorreu um erro inesperado'}
            </p>
            <Button onClick={this.handleReset} variant="outline" className="w-full">
              Tentar novamente
            </Button>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

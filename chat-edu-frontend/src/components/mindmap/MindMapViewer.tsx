import { useEffect, useRef, useState } from 'react';
import type { MindMapData } from '@/types';
import { Card } from '@/components/ui/card';
import { AlertCircle } from 'lucide-react';

interface MindMapViewerProps {
  data: MindMapData;
}

export const MindMapViewer = ({ data }: MindMapViewerProps) => {
  const canvasRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log('MindMapViewer renderizando com dados:', data);
    
    if (!canvasRef.current) {
      console.error('Canvas ref não disponível');
      setError('Erro ao inicializar visualização');
      return;
    }
    
    if (!data.nodes || data.nodes.length === 0) {
      console.error('Nenhum nó para renderizar');
      setError('Nenhum dado para visualizar');
      return;
    }

    try {

    // Limpar canvas
    canvasRef.current.innerHTML = '';

    // Criar visualização simples do mapa mental
    const container = canvasRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Criar SVG
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', width.toString());
    svg.setAttribute('height', height.toString());
    svg.style.width = '100%';
    svg.style.height = '100%';

    // Criar grupo para zoom/pan
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    svg.appendChild(g);

    // Desenhar arestas primeiro (para ficarem atrás dos nós)
    data.edges.forEach((edge) => {
      const sourceNode = data.nodes.find((n) => n.id === edge.source);
      const targetNode = data.nodes.find((n) => n.id === edge.target);

      if (sourceNode && targetNode) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', sourceNode.position.x.toString());
        line.setAttribute('y1', sourceNode.position.y.toString());
        line.setAttribute('x2', targetNode.position.x.toString());
        line.setAttribute('y2', targetNode.position.y.toString());
        line.setAttribute('stroke', 'hsl(var(--muted-foreground))');
        line.setAttribute('stroke-width', '2');
        line.setAttribute('opacity', '0.3');
        g.appendChild(line);
      }
    });

    // Desenhar nós
    data.nodes.forEach((node, index) => {
      const isRoot = node.type === 'input' || index === 0;
      const nodeGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      nodeGroup.setAttribute('transform', `translate(${node.position.x}, ${node.position.y})`);

      // Círculo do nó
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('r', isRoot ? '50' : '40');
      circle.setAttribute('fill', isRoot ? 'hsl(var(--primary))' : 'hsl(var(--secondary))');
      circle.setAttribute('stroke', 'hsl(var(--background))');
      circle.setAttribute('stroke-width', '3');
      circle.style.cursor = 'pointer';
      circle.style.transition = 'all 0.3s ease';

      // Hover effect
      circle.addEventListener('mouseenter', () => {
        circle.setAttribute('r', isRoot ? '55' : '45');
        circle.setAttribute('opacity', '0.8');
      });
      circle.addEventListener('mouseleave', () => {
        circle.setAttribute('r', isRoot ? '50' : '40');
        circle.setAttribute('opacity', '1');
      });

      nodeGroup.appendChild(circle);

      // Texto do nó
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('dy', '0.3em');
      text.setAttribute('fill', 'hsl(var(--primary-foreground))');
      text.setAttribute('font-size', isRoot ? '14' : '12');
      text.setAttribute('font-weight', isRoot ? 'bold' : 'normal');
      text.style.pointerEvents = 'none';
      text.style.userSelect = 'none';

      // Quebrar texto longo
      const label = node.data.label;
      const maxChars = isRoot ? 15 : 12;
      if (label.length > maxChars) {
        const words = label.split(' ');
        let line = '';
        let lineNumber = 0;
        const lineHeight = 1.2;

        words.forEach((word) => {
          const testLine = line + word + ' ';
          if (testLine.length > maxChars && line !== '') {
            const tspan = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
            tspan.setAttribute('x', '0');
            tspan.setAttribute('dy', lineNumber === 0 ? '-0.6em' : `${lineHeight}em`);
            tspan.textContent = line.trim();
            text.appendChild(tspan);
            line = word + ' ';
            lineNumber++;
          } else {
            line = testLine;
          }
        });

        if (line) {
          const tspan = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
          tspan.setAttribute('x', '0');
          tspan.setAttribute('dy', lineNumber === 0 ? '0' : `${lineHeight}em`);
          tspan.textContent = line.trim();
          text.appendChild(tspan);
        }
      } else {
        text.textContent = label;
      }

      nodeGroup.appendChild(text);
      g.appendChild(nodeGroup);
    });

    container.appendChild(svg);

    // Adicionar zoom e pan básico
    let isPanning = false;
    let startX = 0;
    let startY = 0;
    let translateX = 0;
    let translateY = 0;
    let scale = 1;

    svg.addEventListener('mousedown', (e) => {
      isPanning = true;
      startX = e.clientX - translateX;
      startY = e.clientY - translateY;
      svg.style.cursor = 'grabbing';
    });

    svg.addEventListener('mousemove', (e) => {
      if (!isPanning) return;
      translateX = e.clientX - startX;
      translateY = e.clientY - startY;
      g.setAttribute('transform', `translate(${translateX}, ${translateY}) scale(${scale})`);
    });

    svg.addEventListener('mouseup', () => {
      isPanning = false;
      svg.style.cursor = 'grab';
    });

    svg.addEventListener('mouseleave', () => {
      isPanning = false;
      svg.style.cursor = 'grab';
    });

    svg.addEventListener('wheel', (e) => {
      e.preventDefault();
      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      scale *= delta;
      scale = Math.max(0.5, Math.min(3, scale));
      g.setAttribute('transform', `translate(${translateX}, ${translateY}) scale(${scale})`);
    });

    svg.style.cursor = 'grab';

    } catch (err) {
      console.error('Erro ao renderizar mapa mental:', err);
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
    }

    return () => {
      if (canvasRef.current) {
        canvasRef.current.innerHTML = '';
      }
    };
  }, [data]);

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <Card className="max-w-md p-6 space-y-4">
          <div className="flex items-center gap-3 text-destructive">
            <AlertCircle className="w-6 h-6" />
            <h3 className="text-lg font-semibold">Erro na visualização</h3>
          </div>
          <p className="text-sm text-muted-foreground">{error}</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex-1 relative bg-muted/20">
      <div ref={canvasRef} className="absolute inset-0" />
      
      <Card className="absolute bottom-4 left-4 p-3 bg-card/95 backdrop-blur">
        <div className="text-xs space-y-1">
          <p className="font-semibold text-foreground">Controles:</p>
          <p className="text-muted-foreground">• Arraste para mover</p>
          <p className="text-muted-foreground">• Scroll para zoom</p>
          <p className="text-muted-foreground">• Hover nos nós para destacar</p>
        </div>
      </Card>
    </div>
  );
};

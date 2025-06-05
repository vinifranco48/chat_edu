import React, { useState, useEffect, useCallback, useRef } from 'react';
import ReactFlow, {
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  addEdge,
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';
import './MindMapInterface.css'; 
import CustomMindMapNode from './CustomMindMapNode';

import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const nodeTypes = { 
  default: CustomMindMapNode,
  input: CustomMindMapNode 
};

const getLayoutedElements = (nodes, edges) => {
  if (!nodes || nodes.length === 0) {
    return { nodes: [], edges: edges || [] };
  }

  const nodeWidth = 220; 
  const nodeHeight = 100; 
  const nodeMarginX = 60;
  const nodeMarginY = 120;

  const layoutedNodes = [];
  const levels = {};      
  const nodeDepths = {}; 

  let rootNode = nodes.find(n => n.type === 'input' || n.id === 'root');
  if (!rootNode && nodes.length > 0) {
    rootNode = nodes[0];
  }

  if (!rootNode) {
    return { nodes, edges: edges || [] };
  }

  const queue = [{ nodeId: rootNode.id, depth: 0 }];
  const visited = new Set(); 

  visited.add(rootNode.id);
  nodeDepths[rootNode.id] = 0;
  levels[0] = [rootNode.id]; 

  let head = 0;
  while(head < queue.length) { 
    const { nodeId, depth } = queue[head++]; 
    
    const childrenEdges = (edges || []).filter(e => e.source === nodeId);
    const childrenNodeIds = childrenEdges.map(e => e.target);

    childrenNodeIds.forEach(childId => {
      if (!visited.has(childId)) {
        const childNodeExists = nodes.find(n => n.id === childId);
        if (childNodeExists) { 
            visited.add(childId);
            nodeDepths[childId] = depth + 1;
            if (!levels[depth + 1]) {
              levels[depth + 1] = [];
            }
            levels[depth + 1].push(childId);
            queue.push({ nodeId: childId, depth: depth + 1 });
        }
      }
    });
  }
  
  Object.keys(levels).sort((a,b) => parseInt(a) - parseInt(b)).forEach(levelKey => {
    const level = parseInt(levelKey);
    const nodesInLevel = levels[level];
    const levelWidth = (nodesInLevel.length * (nodeWidth + nodeMarginX)) - nodeMarginX;
    
    nodesInLevel.forEach((nodeId, indexInLevel) => {
        const node = nodes.find(n => n.id === nodeId);
        if (node) {
            const x = (indexInLevel * (nodeWidth + nodeMarginX)) - (levelWidth / 2) + (nodeWidth / 2);
            const y = level * (nodeHeight + nodeMarginY);
            if (!layoutedNodes.find(ln => ln.id === node.id)) {
                 layoutedNodes.push({ ...node, position: { x, y } });
            }
        }
    });
  });

  nodes.forEach(originalNode => {
    if (!layoutedNodes.find(ln => ln.id === originalNode.id)) {
      layoutedNodes.push({ ...originalNode, position: originalNode.position || { x: 0, y: 0 } });
    }
  });

  return { nodes: layoutedNodes, edges: edges || [] };
};

// Modal para editar nós
function NodeEditModal({ node, isOpen, onClose, onSave }) {
  const [label, setLabel] = useState('');
  const [description, setDescription] = useState('');
  const [annotation, setAnnotation] = useState('');

  useEffect(() => {
    if (node && isOpen) {
      setLabel(node.data?.label || '');
      setDescription(node.data?.description || '');
      setAnnotation(node.data?.annotation || '');
    }
  }, [node, isOpen]);

  const handleSave = () => {
    onSave({
      ...node,
      data: {
        ...node.data,
        label,
        description,
        annotation
      }
    });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '20px',
        borderRadius: '8px',
        minWidth: '400px',
        maxWidth: '600px'
      }}>
        <h3>Editar Nó</h3>
        
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Título:
          </label>
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #ddd',
              borderRadius: '4px'
            }}
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Descrição:
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              resize: 'vertical'
            }}
          />
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Anotação Pessoal:
          </label>
          <textarea
            value={annotation}
            onChange={(e) => setAnnotation(e.target.value)}
            rows={3}
            placeholder="Adicione suas anotações pessoais aqui..."
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              resize: 'vertical',
              backgroundColor: '#f9f9f9'
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
          <button
            onClick={onClose}
            style={{
              padding: '8px 16px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              backgroundColor: 'white',
              cursor: 'pointer'
            }}
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            style={{
              padding: '8px 16px',
              border: 'none',
              borderRadius: '4px',
              backgroundColor: '#007bff',
              color: 'white',
              cursor: 'pointer'
            }}
          >
            Salvar
          </button>
        </div>
      </div>
    </div>
  );
}

// Modal para adicionar novo nó
function AddNodeModal({ isOpen, onClose, onAdd, parentNode, position }) {
  const [label, setLabel] = useState('');
  const [description, setDescription] = useState('');
  const [annotation, setAnnotation] = useState('');

  useEffect(() => {
    if (isOpen) {
      setLabel('');
      setDescription('');
      setAnnotation('');
    }
  }, [isOpen]);

  const handleAdd = () => {
    if (!label.trim()) {
      alert('Por favor, insira um título para o nó');
      return;
    }

    const newNodeId = `node-${Date.now()}`;
    const newNode = {
      id: newNodeId,
      type: 'default',
      position: position || { x: Math.random() * 500, y: Math.random() * 500 },
      data: {
        label: label.trim(),
        description: description.trim(),
        annotation: annotation.trim()
      }
    };

    onAdd(newNode, parentNode);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '20px',
        borderRadius: '8px',
        minWidth: '400px',
        maxWidth: '600px'
      }}>
        <h3>Adicionar Novo Nó</h3>
        {parentNode && (
          <p style={{ color: '#666', marginBottom: '15px' }}>
            Será conectado a: <strong>{parentNode.data?.label}</strong>
          </p>
        )}
        
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Título: *
          </label>
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #ddd',
              borderRadius: '4px'
            }}
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Descrição:
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              resize: 'vertical'
            }}
          />
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Anotação Pessoal:
          </label>
          <textarea
            value={annotation}
            onChange={(e) => setAnnotation(e.target.value)}
            rows={3}
            placeholder="Adicione suas anotações pessoais aqui..."
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              resize: 'vertical',
              backgroundColor: '#f9f9f9'
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
          <button
            onClick={onClose}
            style={{
              padding: '8px 16px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              backgroundColor: 'white',
              cursor: 'pointer'
            }}
          >
            Cancelar
          </button>
          <button
            onClick={handleAdd}
            style={{
              padding: '8px 16px',
              border: 'none',
              borderRadius: '4px',
              backgroundColor: '#28a745',
              color: 'white',
              cursor: 'pointer'
            }}
          >
            Adicionar
          </button>
        </div>
      </div>
    </div>
  );
}

const MindMapDisplayComponent = ({ initialNodes, initialEdges, onNodesUpdate, isEditMode }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [contextMenu, setContextMenu] = useState(null);
  const [clickPosition, setClickPosition] = useState(null);
  const reactFlowInstance = useReactFlow();


  useEffect(() => {
    if (initialNodes && Array.isArray(initialNodes) && initialNodes.length > 0) {
        const nodesWithEnsuredDataAndType = initialNodes.map(n => ({
            ...n,
            type: n.type || (n.id === 'root' ? 'input' : 'default'),
            data: n.data || { label: n.id, description: "Dados do nó ausentes", annotation: "" },
            position: n.position 
        }));

        const needsLayout = nodesWithEnsuredDataAndType.some(n => !n.position || (n.position.x === 0 && n.position.y === 0 && nodesWithEnsuredDataAndType.length > 1));
        if (needsLayout) {
            const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(nodesWithEnsuredDataAndType, initialEdges || []);
            setNodes(layoutedNodes || []);
            setEdges(layoutedEdges || []);
        } else {
            setNodes(nodesWithEnsuredDataAndType);
            setEdges(initialEdges || []);
        }
    } else {
        setNodes([]);
        setEdges([]);
    }
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const onConnect = useCallback((params) => {
    if (isEditMode) {
      setEdges((eds) => addEdge(params, eds));
      onNodesUpdate?.(nodes, addEdge(params, edges)); // Notificar atualização de arestas também
    }
  }, [isEditMode, setEdges, nodes, edges, onNodesUpdate]);

  const onNodeClick = useCallback((event, node) => {
    if (isEditMode) {
      setSelectedNode(node);
      setEditModalOpen(true);
    }
  }, [isEditMode]);

  const onNodeContextMenu = useCallback((event, node) => {
    if (isEditMode) {
      event.preventDefault();
      setContextMenu({
        x: event.clientX,
        y: event.clientY,
        node
      });
    }
  }, [isEditMode]);

  const onPaneClick = useCallback((event) => {
    setContextMenu(null);
    if (isEditMode && event.detail === 2) { // Double click
      const screenPosition = { x: event.clientX, y: event.clientY };
      const flowPosition = reactFlowInstance.screenToFlowPosition(screenPosition);
      setClickPosition(flowPosition);
      setSelectedNode(null); // Nenhum nó pai se clicar no painel
      setAddModalOpen(true);
    }
  }, [isEditMode, reactFlowInstance]);

  const handleNodeSave = useCallback((updatedNode) => {
    const newNodes = nodes.map((node) => node.id === updatedNode.id ? updatedNode : node);
    setNodes(newNodes);
    onNodesUpdate?.(newNodes, edges);
  }, [nodes, edges, onNodesUpdate, setNodes]);

  const handleNodeAdd = useCallback((newNode, parentNode) => {
    const newNodes = [...nodes, newNode];
    setNodes(newNodes);
    
    let newEdges = edges;
    if (parentNode) {
      const newEdge = {
        id: `edge-${parentNode.id}-${newNode.id}`,
        source: parentNode.id,
        target: newNode.id,
        type: 'default' // ou 'smoothstep', 'step', 'straight'
      };
      newEdges = [...edges, newEdge];
      setEdges(newEdges);
    }
    
    onNodesUpdate?.(newNodes, newEdges);
  }, [nodes, edges, onNodesUpdate, setNodes, setEdges]);

  const handleDeleteNode = useCallback((nodeToDelete) => {
    const newNodes = nodes.filter((node) => node.id !== nodeToDelete.id);
    const newEdges = edges.filter((edge) => edge.source !== nodeToDelete.id && edge.target !== nodeToDelete.id);
    setNodes(newNodes);
    setEdges(newEdges);
    setContextMenu(null);
    onNodesUpdate?.(newNodes, newEdges);
  }, [nodes, edges, setNodes, setEdges, onNodesUpdate]);

  if (!nodes || nodes.length === 0) {
    return (
      <div className="mindmap-placeholder" style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100%',
        width: '100%'
      }}>
        {isEditMode ? 
          'Nenhum nó para exibir. Clique duas vezes no painel para adicionar um nó.' :
          'Nenhum nó para exibir no mapa (MindMapDisplay).'
        }
      </div>
    );
  }

  return (
    <div style={{ height: '100%', width: '100%' }} data-testid="rf-wrapper"> {/* Adicionado data-testid */}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onNodeContextMenu={onNodeContextMenu}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes} 
        fitView
        fitViewOptions={{ padding: 0.2 }}
        attributionPosition="top-right"
        minZoom={0.1}
        maxZoom={2}
      >
        <Controls />
        <MiniMap nodeStrokeWidth={3} zoomable pannable />
        <Background variant="dots" gap={12} size={1} />
      </ReactFlow>

      {/* Context Menu */}
      {contextMenu && (
        <div
          style={{
            position: 'fixed',
            top: contextMenu.y,
            left: contextMenu.x,
            backgroundColor: 'white',
            border: '1px solid #ddd',
            borderRadius: '4px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
            zIndex: 1000,
            padding: '5px 0' // Adicionado padding
          }}
        >
          <button
            onClick={() => {
              setSelectedNode(contextMenu.node); // Define o nó pai para o novo nó
              const parentNodePos = contextMenu.node.position;
              // Calcular uma posição para o nó filho, abaixo do pai
              const childNodePos = {
                x: parentNodePos.x,
                y: parentNodePos.y + (contextMenu.node.height || 100) + 50 // Ajustar conforme o tamanho do nó
              };
              setClickPosition(childNodePos); // Posição para o novo nó filho
              setAddModalOpen(true);
              setContextMenu(null);
            }}
            style={{
              display: 'block',
              width: '100%',
              padding: '8px 16px',
              border: 'none',
              backgroundColor: 'transparent',
              textAlign: 'left',
              cursor: 'pointer',
                  hover: { backgroundColor: '#f0f0f0' }
            }}
          >
            Adicionar nó filho
          </button>
          <button
            onClick={() => handleDeleteNode(contextMenu.node)}
            style={{
              display: 'block',
              width: '100%',
              padding: '8px 16px',
              border: 'none',
              backgroundColor: 'transparent',
              textAlign: 'left',
              cursor: 'pointer',
              color: 'red',
                  hover: { backgroundColor: '#f0f0f0' }
            }}
          >
            Excluir nó
          </button>
        </div>
      )}

      {/* Modals */}
      <NodeEditModal
        node={selectedNode}
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        onSave={handleNodeSave}
      />

      <AddNodeModal
        isOpen={addModalOpen}
        onClose={() => { setAddModalOpen(false); setSelectedNode(null); /* Limpa o nó pai selecionado */ }}
        onAdd={handleNodeAdd}
        parentNode={selectedNode}
        position={clickPosition}
      />
    </div>
  );
}


// Envolver MindMapDisplay com ReactFlowProvider
const MindMapDisplay = (props) => (
  <ReactFlowProvider>
    <MindMapDisplayComponent {...props} />
  </ReactFlowProvider>
);


function MindMapInterface({ selectedCourse, isDarkMode }) {
  const [mindMapData, setMindMapData] = useState({ nodes: [], edges: [] });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isEditMode, setIsEditMode] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const mindMapRef = useRef(null); // Ref para o contêiner do ReactFlow

  useEffect(() => {
    if (selectedCourse && selectedCourse.id) {
      setIsLoading(true);
      setError(null); 
      const courseName = selectedCourse.nome || selectedCourse.name || `Curso ${selectedCourse.id}`;
      const targetUrl = `${API_BASE_URL}/mindmaps/${selectedCourse.id}?course_name=${encodeURIComponent(courseName)}`;
      
      console.log("%c[MindMapInterface DEBUG] Tentando buscar de:", "color: blue; font-weight: bold;", targetUrl);

      fetch(targetUrl, {
        method: 'POST', // Ou GET se for para buscar e o backend estiver configurado assim
        headers: { 'Content-Type': 'application/json' },
        // body: JSON.stringify({ course_name: courseName }) // Se o POST precisar de um corpo
      })
        .then(response => {
          if (!response.ok) {
            return response.json().then(errData => {
              const errorMessage = errData.detail || `Erro ${response.status} (${response.statusText})`;
              throw new Error(errorMessage);
            }).catch(async (jsonError) => { 
                try {
                    const responseText = await response.text();
                    throw new Error(`Erro ${response.status} (${response.statusText}). Resposta não é JSON. Preview: ${responseText.substring(0,200)}`);
                  } catch (textError) {
                    throw new Error(`Erro ${response.status} (${response.statusText}). Falha ao ler corpo da resposta.`);
                  }
            });
          }
          return response.json();
        })
        .then(data => {
          if (data && data.nodes && Array.isArray(data.nodes) && data.edges && Array.isArray(data.edges)) {
            const processedNodes = data.nodes.map(n => ({
                ...n, 
                type: n.type || (n.id === 'root' ? 'input' : 'default'),
                data: { 
                    label: n.data?.label || n.id, 
                    description: n.data?.description || "",
                    annotation: n.data?.annotation || ""
                },
                position: n.position, 
            }));
            setMindMapData({ nodes: processedNodes, edges: data.edges });
            setHasChanges(false); // Resetar hasChanges após carregar
          } else {
            console.warn("[MindMapInterface WARNING] Dados do mapa mental recebidos em formato inesperado ou estrutura inválida:", data);
            setMindMapData({ nodes: [], edges: [] });
          }
        })
        .catch(err => {
          console.error("[MindMapInterface ERROR] Falha na requisição ou processamento do mapa mental:", err);
          setError(err.message);
          setMindMapData({ nodes: [], edges: [] });
        })
        .finally(() => {
          setIsLoading(false);
        });
    } else {
      // Limpar dados se nenhum curso estiver selecionado
      setMindMapData({ nodes: [], edges: [] });
      setIsLoading(false);
      setError(null);
      setHasChanges(false);
    }
  }, [selectedCourse]);

  // useEffect(() => { // Este useEffect parece redundante com a lógica no final do useEffect acima
  //   if (!selectedCourse || !selectedCourse.id) {
  //     setMindMapData({ nodes: [], edges: [] });
  //     setIsLoading(false); 
  //     setError(null);    
  //   }
  // }, [selectedCourse]); 

  const handleElementsUpdate = useCallback((updatedNodes, updatedEdges) => {
    setMindMapData({ nodes: updatedNodes, edges: updatedEdges });
    setHasChanges(true);
  }, []);

  const exportToPDF = async () => {
    const reactFlowPane = document.querySelector('.react-flow__pane'); // Seleciona o painel do ReactFlow
    if (!reactFlowPane) {
        alert('Erro: Não foi possível encontrar o mapa mental para exportar. O painel ReactFlow não foi encontrado.');
        console.error('Elemento .react-flow__pane não encontrado para exportação PDF.');
        return;
    }

    try {
      const canvas = await html2canvas(reactFlowPane, {
        backgroundColor: isDarkMode ? '#1a1a1a' : '#ffffff',
        scale: 2,
        useCORS: true,
        allowTaint: true,
        logging: true, // Habilitar logs do html2canvas para debugging
        onclone: (document) => { // Remover controles e minimapa da exportação
            const controls = document.querySelector('.react-flow__controls');
            if (controls) controls.style.display = 'none';
            const minimap = document.querySelector('.react-flow__minimap');
            if (minimap) minimap.style.display = 'none';
        }
      });

      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF({
        orientation: canvas.width > canvas.height ? 'landscape' : 'portrait',
        unit: 'mm',
        format: 'a4'
      });

      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      const imgWidth = canvas.width;
      const imgHeight = canvas.height;
      const ratio = Math.min((pdfWidth - 20) / imgWidth, (pdfHeight - 30) / imgHeight); // Deixar margens
      const imgX = (pdfWidth - imgWidth * ratio) / 2;
      const imgY = 20; // Margem superior para o título

      pdf.setFontSize(16);
      const courseTitle = selectedCourse?.nome || selectedCourse?.name || 'Curso';
      pdf.text(`Mapa Mental: ${courseTitle}`, pdfWidth / 2, 15, { align: 'center' });
      
      pdf.addImage(imgData, 'PNG', imgX, imgY, imgWidth * ratio, imgHeight * ratio);

      const fileName = `mapa-mental-${courseTitle.replace(/\s+/g, '_').toLowerCase()}-${new Date().toISOString().split('T')[0]}.pdf`;
      pdf.save(fileName);

    } catch (error) {
      console.error('Erro ao exportar PDF:', error);
      alert('Erro ao exportar PDF. Verifique o console para mais detalhes.');
    }
  };

  const saveChanges = async () => {
    if (!selectedCourse || !selectedCourse.id) {
        alert('Nenhum curso selecionado para salvar.');
        return;
    }
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/mindmaps/${selectedCourse.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mindMapData) // Envia nós e arestas
      });

      if (response.ok) {
        setHasChanges(false);
        alert('Alterações salvas com sucesso!');
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Erro ao salvar. Resposta não é JSON.' }));
        throw new Error(errorData.detail || `Erro ${response.status} ao salvar.`);
      }
    } catch (error) {
      console.error('Erro ao salvar:', error);
      alert(`Erro ao salvar as alterações: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  if (!selectedCourse) {
    return (
      <div className="mindmap-container" style={{
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center',
        height: '400px', // Altura pode ser ajustada conforme necessário
        width: '100%'
      }}>
        <p>Selecione um curso para ver o mapa mental.</p>
      </div>
    );
  }

  if (isLoading && !(isEditMode && hasChanges)) { // Não mostrar loading global se for apenas salvando em background
    return (
      <div className="mindmap-container" style={{
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center',
        height: '400px',
        width: '100%'
      }}>
        <p>Carregando mapa mental...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mindmap-container mindmap-error" style={{
        display: 'flex', 
        flexDirection: 'column',
        justifyContent: 'center', 
        alignItems: 'center',
        height: '400px',
        width: '100%',
        padding: '20px',
        boxSizing: 'border-box'
      }}>
        <p style={{ color: 'red', fontWeight: 'bold' }}>Erro ao carregar o mapa mental:</p>
        <p style={{ color: 'red', wordBreak: 'break-word' }}>{error}</p>
        <button onClick={() => setError(null)} style={{marginTop: '10px'}}>Tentar novamente</button>
      </div>
    );
  }
  
  return (
    <div 
        ref={mindMapRef} // Adiciona a ref aqui
        className={`mindmap-container ${isDarkMode ? 'dark' : 'light'}`} 
        style={{
          height: 'calc(100vh - 150px)', // Exemplo de altura dinâmica
          minHeight: '500px',
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          border: '1px solid #eee', // Borda para o container principal
          borderRadius: '8px'
        }}
    >
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        padding: '10px 15px', // Padding para a barra de título/controles
        borderBottom: `1px solid ${isDarkMode ? '#333' : '#ddd'}`,
        flexShrink: 0
      }}>
        <h2 style={{ 
          fontSize: '1.2em',
          fontWeight: 'bold',
          margin: 0
        }}>
          Mapa Mental: {selectedCourse?.nome || selectedCourse?.name || selectedCourse?.id}
        </h2>
        
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          {isEditMode && hasChanges && (
            <span style={{ color: '#ffa500', fontSize: '12px', fontWeight: 'bold' }}>
              Alterações não salvas!
            </span>
          )}
          
          <button
            onClick={() => setIsEditMode(!isEditMode)}
            title={isEditMode ? 'Sair do modo de edição' : 'Entrar no modo de edição'}
            style={{
              padding: '6px 12px',
              border: `1px solid ${isEditMode ? '#dc3545' : '#007bff'}`,
              borderRadius: '4px',
              backgroundColor: isEditMode ? '#dc3545' : '#007bff',
              color: 'white',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            {isEditMode ? 'Sair da Edição' : 'Editar Mapa'}
          </button>

          {isEditMode && ( // Botão Salvar sempre visível no modo de edição, desabilitado se não houver mudanças
            <button
              onClick={saveChanges}
                  disabled={!hasChanges || isLoading} // Desabilitar se não houver mudanças ou estiver carregando
              title={hasChanges ? "Salvar alterações no servidor" : "Nenhuma alteração para salvar"}
              style={{
                padding: '6px 12px',
                border: 'none',
                borderRadius: '4px',
                backgroundColor: hasChanges ? '#28a745' : '#6c757d', // Verde se houver mudanças, cinza senão
                color: 'white',
                cursor: hasChanges && !isLoading ? 'pointer' : 'not-allowed',
                fontSize: '12px',
                  opacity: hasChanges && !isLoading ? 1 : 0.7
              }}
            >
              {isLoading && hasChanges ? 'Salvando...' : 'Salvar'}
            </button>
          )}

          <button
            onClick={exportToPDF}
            title="Exportar o mapa mental atual como PDF"
            style={{
              padding: '6px 12px',
              border: '1px solid #17a2b8', // Cor informativa
              borderRadius: '4px',
              backgroundColor: 'transparent',
              color: '#17a2b8',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            📄 Exportar PDF
          </button>
        </div>
      </div>

      <div style={{ flexGrow: 1, position: 'relative' }}> {/* Container para o ReactFlow ocupar o espaço restante */}
        <MindMapDisplay
            initialNodes={mindMapData.nodes}
            initialEdges={mindMapData.edges}
            onNodesUpdate={handleElementsUpdate} // Passar a função de atualização combinada
            isEditMode={isEditMode}
        />
      </div>

      {isEditMode && (
        <div style={{
          padding: '10px',
          backgroundColor: isDarkMode ? '#2a2a2a' : '#e7f3ff',
          border: `1px solid ${isDarkMode ? '#444' : '#b3d7ff'}`,
          borderRadius: '4px',
          marginTop: '10px',
          margin: '10px 15px', // Para alinhar com o padding da barra de título
          textAlign: 'left', // Alinhar à esquerda para lista
          fontSize: '13px',
          color: isDarkMode ? '#ccc' : '#004085',
          flexShrink: 0 // Para não encolher
        }}>
          <strong style={{ display: 'block', marginBottom: '5px' }}>Modo de Edição Ativo:</strong>
          <ul style={{ listStylePosition: 'inside', paddingLeft: '0', margin: 0, fontSize: '12px' }}>
            <li>Clique em um nó para editar.</li>
            <li>Clique com o botão direito em um nó para adicionar filhos ou excluir.</li>
            <li>Clique duas vezes no painel para adicionar um novo nó.</li>
            <li>Arraste de um nó para outro para criar conexões.</li>
          </ul>
        </div>
      )}
    </div>
  );
}

export default MindMapInterface;
import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import './CustomMindMapNode.css'; // Vamos criar este CSS abaixo

const CustomMindMapNode = ({ data, isConnectable, selected, type }) => {
  return (
    <div className={`custom-mind-map-node ${selected ? 'selected' : ''} node-type-${type || 'default'}`}>
      {/* Handles podem ser ajustados (ex: apenas Top/Bottom ou Left/Right) */}
      <Handle type="target" position={Position.Top} isConnectable={isConnectable} id="target-top" />
      <Handle type="target" position={Position.Left} isConnectable={isConnectable} id="target-left" />
      
      <div className="node-content-wrapper">
        {data.label && <h4 className="node-label">{data.label}</h4>}
        {data.description && (
          <p className="node-description">{data.description}</p>
        )}
      </div>
      
      <Handle type="source" position={Position.Bottom} isConnectable={isConnectable} id="source-bottom" />
      <Handle type="source" position={Position.Right} isConnectable={isConnectable} id="source-right" />
    </div>
  );
};

export default memo(CustomMindMapNode);
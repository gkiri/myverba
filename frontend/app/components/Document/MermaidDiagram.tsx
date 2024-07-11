import React, { useEffect, useRef, useState, useCallback } from 'react';
import mermaid from 'mermaid';
import { motion } from 'framer-motion';
import { FaEdit, FaCheck, FaTimes, FaPlus, FaMinus, FaUndo, FaDownload, FaCopy } from 'react-icons/fa';

interface MermaidDiagramProps {
  code: string;
}

const MermaidDiagram: React.FC<MermaidDiagramProps> = ({ code: initialCode }) => {
  const [svg, setSvg] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const [isEditing, setIsEditing] = useState(false);
  const [editableCode, setEditableCode] = useState(initialCode);
  const containerRef = useRef<HTMLDivElement>(null);
  const editorRef = useRef<HTMLTextAreaElement>(null);

  const initializeMermaid = useCallback(() => {
    mermaid.initialize({ 
      startOnLoad: true, 
      theme: 'default',
      securityLevel: 'loose',
      flowchart: { useMaxWidth: false, htmlLabels: true },
      er: { useMaxWidth: false },
      sequence: { useMaxWidth: false },
      gantt: { useMaxWidth: false },
      journey: { useMaxWidth: false }
    });
  }, []);

  useEffect(() => {
    initializeMermaid();
    renderDiagram(initialCode);
  }, [initialCode, initializeMermaid]);

  const sanitizeMermaidCode = (code: string) => {
    let cleanCode = code.replace(/```mermaid\n?/, '').replace(/```$/, '').trim();
    const diagramType = detectDiagramType(cleanCode);
    
    switch (diagramType) {
      case 'flowchart':
        cleanCode = sanitizeFlowchart(cleanCode);
        break;
      case 'sequenceDiagram':
        cleanCode = sanitizeSequenceDiagram(cleanCode);
        break;
      default:
        cleanCode = cleanCode.replace(/[&<>]/g, '');
    }
    
    return cleanCode;
  };

  const detectDiagramType = (code: string) => {
    const firstLine = code.split('\n')[0].trim().toLowerCase();
    if (firstLine.startsWith('graph') || firstLine.startsWith('flowchart')) return 'flowchart';
    if (firstLine.startsWith('sequencediagram')) return 'sequenceDiagram';
    if (firstLine.startsWith('classDiagram')) return 'classDiagram';
    if (firstLine.startsWith('stateDiagram')) return 'stateDiagram';
    if (firstLine.startsWith('erDiagram')) return 'erDiagram';
    if (firstLine.startsWith('gantt')) return 'gantt';
    if (firstLine.startsWith('pie')) return 'pie';
    return 'unknown';
  };

  const sanitizeFlowchart = (code: string) => {
    let cleanCode = code;
    if (!cleanCode.startsWith('graph') && !cleanCode.startsWith('flowchart')) {
      cleanCode = 'graph LR\n' + cleanCode;
    }
    // Fix arrow syntax: remove spaces around arrows and standardize to -->
    cleanCode = cleanCode.replace(/\s*-+\s*>\s*/g, '-->');
    cleanCode = cleanCode.replace(/\s*=+\s*>\s*/g, '==>');
    cleanCode = cleanCode.replace(/\s*-+\s*\|\s*/g, '--|');
    cleanCode = cleanCode.replace(/\s*\|\s*-+\s*/g, '|--');
    
    // Ensure proper spacing around node definitions
    cleanCode = cleanCode.replace(/\[([^\]]+)\]/g, '[$1]');
    
    // Remove any duplicate spaces
    cleanCode = cleanCode.replace(/\s+/g, ' ');
    
    // Ensure each statement is on a new line
    cleanCode = cleanCode.split(' ').join('\n');
    
    return cleanCode;
  };
  
  const sanitizeSequenceDiagram = (code: string) => {
    let cleanCode = code;
    if (!cleanCode.startsWith('sequenceDiagram')) {
      cleanCode = 'sequenceDiagram\n' + cleanCode;
    }
    cleanCode = cleanCode.replace(/->/g, '->');
    cleanCode = cleanCode.replace(/<-/g, '<-');
    return cleanCode;
  };

  const renderDiagram = async (codeToRender: string) => {
    try {
      const sanitizedCode = sanitizeMermaidCode(codeToRender);
      console.log('Sanitized Mermaid code:', sanitizedCode);
      const { svg } = await mermaid.render('mermaid-diagram', sanitizedCode);
      setSvg(svg);
      setError(null);
    } catch (err) {
      console.error('Mermaid rendering error:', err);
      setError(`Failed to render diagram. Error: ${err.message}\n\nTry editing the diagram code to fix the issue.`);
      setSvg('');
    }
  };

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.1, 2));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.1, 0.5));
  const handleResetZoom = () => setZoom(1);

  const handleEditToggle = () => {
    setIsEditing(!isEditing);
    if (!isEditing) {
      setEditableCode(sanitizeMermaidCode(initialCode));
    }
  };

  const handleCodeChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setEditableCode(e.target.value);
  };

  const handleCodeSubmit = () => {
    renderDiagram(editableCode);
    setIsEditing(false);
  };

  const handleDownload = () => {
    const svgBlob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' });
    const svgUrl = URL.createObjectURL(svgBlob);
    const downloadLink = document.createElement('a');
    downloadLink.href = svgUrl;
    downloadLink.download = 'mermaid_diagram.svg';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(editableCode).then(() => {
      alert('Diagram code copied to clipboard!');
    }).catch(err => {
      console.error('Failed to copy code:', err);
    });
  };

  return (
    <motion.div 
      className="bg-bg-alt-verba rounded-lg p-6 shadow-lg"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <h2 className="text-2xl font-bold mb-4 text-primary-verba">Visualization</h2>
      <div className="mb-4 flex justify-between items-center flex-wrap gap-2">
        <div className="space-x-2">
          <button onClick={handleZoomIn} className="btn btn-sm bg-secondary-verba text-text-verba" title="Zoom In">
            <FaPlus />
          </button>
          <button onClick={handleZoomOut} className="btn btn-sm bg-secondary-verba text-text-verba" title="Zoom Out">
            <FaMinus />
          </button>
          <button onClick={handleResetZoom} className="btn btn-sm bg-secondary-verba text-text-verba" title="Reset Zoom">
            <FaUndo />
          </button>
          <button onClick={handleDownload} className="btn btn-sm bg-secondary-verba text-text-verba" title="Download SVG">
            <FaDownload />
          </button>
          <button onClick={handleCopyCode} className="btn btn-sm bg-secondary-verba text-text-verba" title="Copy Code">
            <FaCopy />
          </button>
        </div>
        <button 
          onClick={handleEditToggle} 
          className="btn btn-sm bg-primary-verba text-text-verba flex items-center"
        >
          {isEditing ? <FaTimes className="mr-2" /> : <FaEdit className="mr-2" />}
          {isEditing ? 'Cancel' : 'Edit'}
        </button>
      </div>
      {isEditing ? (
        <div className="mb-4">
          <textarea
            ref={editorRef}
            value={editableCode}
            onChange={handleCodeChange}
            className="w-full h-64 p-2 border border-secondary-verba rounded-lg bg-bg-verba text-text-verba"
          />
          <button 
            onClick={handleCodeSubmit}
            className="mt-2 btn btn-sm bg-primary-verba text-text-verba flex items-center"
          >
            <FaCheck className="mr-2" /> Apply Changes
          </button>
        </div>
      ) : (
        <div 
          ref={containerRef}
          className="overflow-auto border border-secondary-verba rounded-lg p-4"
          style={{ maxHeight: '60vh' }}
        >
          {error ? (
            <div className="text-warning-verba whitespace-pre-wrap">
              <p>{error}</p>
              <p className="mt-2">Raw Mermaid Code:</p>
              <pre className="bg-bg-verba p-2 rounded mt-1 text-sm">{sanitizeMermaidCode(initialCode)}</pre>
            </div>
          ) : (
            <div 
              dangerouslySetInnerHTML={{ __html: svg }} 
              style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}
            />
          )}
        </div>
      )}
    </motion.div>
  );
};

export default MermaidDiagram;

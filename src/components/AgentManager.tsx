import { type CustomAgent } from '../types/agent';
import { useState, useEffect } from 'react';
import { Upload, Trash2, Bot, FileJson, FileCode } from 'lucide-react';
import AgentUploadModal from './AgentUploadModal';
import { getAgents, deleteAgent, toggleAgent, saveAgent } from '@/lib/agent-persistence';

export default function AgentManager() {
  const [agents, setAgents] = useState<CustomAgent[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    getAgents().then(setAgents).catch(console.error);
  }, []);

  const handleUpload = async (agent: CustomAgent) => {
    await saveAgent(agent);
    setAgents((prev) => [...prev, agent]);
    setIsModalOpen(false);
  };

  const handleToggle = async (id: string) => {
    const agent = agents.find((a) => a.id === id);
    if (agent) {
      await toggleAgent(id, !agent.enabled);
      setAgents((prev) =>
        prev.map((a) => (a.id === id ? { ...a, enabled: !a.enabled } : a))
      );
    }
  };

  const handleDelete = async (id: string) => {
    await deleteAgent(id);
    setAgents((prev) => prev.filter((a) => a.id !== id));
  };

  const handleTierChange = (id: string, tier: 'full' | 'reduced' | 'custom') => {
    setAgents((prev) =>
      prev.map((a) => (a.id === id ? { ...a, securityTier: tier } : a))
    );
  };

  return (
    <div className="p-4 rounded-2xl border border-border/30 bg-background/20">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold text-foreground">Custom Agents</h2>
        </div>
        <button
          type="button"
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary/10 text-primary text-xs font-medium hover:bg-primary/20 transition-all"
        >
          <Upload className="w-3.5 h-3.5" />
          Upload Agent
        </button>
      </div>

      {agents.length === 0 ? (
        <p className="text-xs text-muted-foreground text-center py-4">
          No custom agents uploaded yet
        </p>
      ) : (
        <div className="space-y-2">
          {agents.map((agent) => (
            <div
              key={agent.id}
              className="flex items-center gap-3 p-3 rounded-xl bg-background/10"
            >
              <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-primary/10">
                {agent.type === 'config' ? (
                  <FileJson className="w-4 h-4 text-primary" />
                ) : (
                  <FileCode className="w-4 h-4 text-primary" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-foreground truncate">
                  {agent.name}
                </p>
                <p className="text-[10px] text-muted-foreground truncate">
                  {agent.description || agent.type}
                </p>
              </div>
              <select
                value={agent.securityTier}
                onChange={(e) =>
                  handleTierChange(agent.id, e.target.value as 'full' | 'reduced' | 'custom')
                }
                className="text-[10px] bg-transparent border border-border/30 rounded px-1.5 py-0.5 text-muted-foreground"
              >
                <option value="full">Full</option>
                <option value="reduced">Reduced</option>
                <option value="custom">Custom</option>
              </select>
              <button
                type="button"
                onClick={() => handleToggle(agent.id)}
                className={`w-8 h-4 rounded-full transition-all ${
                  agent.enabled ? 'bg-primary' : 'bg-border'
                }`}
              >
                <div
                  className={`w-3 h-3 rounded-full bg-white transition-transform ${
                    agent.enabled ? 'translate-x-4' : 'translate-x-0.5'
                  }`}
                />
              </button>
              <button
                type="button"
                onClick={() => handleDelete(agent.id)}
                className="p-1 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-all"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      {isModalOpen && (
        <AgentUploadModal
          onUpload={handleUpload}
          onClose={() => setIsModalOpen(false)}
        />
      )}
    </div>
  );
}
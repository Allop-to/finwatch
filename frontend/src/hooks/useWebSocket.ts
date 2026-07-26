import { useEffect, useRef } from 'react';
import { useAlertStore } from '@/store/alertStore';
import { toast } from 'sonner';

export function useWebSocket() {
  const addAlert = useAlertStore((s) => s.addAlert);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ws`;
    let retryDelay = 1000;

    function connect() {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      ws.onopen = () => { retryDelay = 1000; };
      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === 'detection.alert') {
          addAlert({ type: 'detection', message: `高危异常: #${msg.data.txn_id}`, detectionId: msg.data.id });
          toast.error('高危异常检测', {
            description: `分数: ${msg.data.score.toFixed(2)}`,
            action: {
              label: '查看',
              onClick: () => { window.location.href = `/detection/${msg.data.id}`; },
            },
          });
        } else if (msg.type === 'budget.warning') {
          toast.warning('预算预警', { description: msg.data });
        }
      };
      ws.onclose = () => {
        setTimeout(connect, retryDelay);
        retryDelay = Math.min(retryDelay * 2, 30000);
      };
    }
    connect();
    return () => wsRef.current?.close();
  }, [addAlert]);
}

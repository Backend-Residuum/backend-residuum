import { formatKg } from '../utils/format';

export default function Inventory({ inventario }) {
  const entries = Object.entries(inventario || {});
  if (!entries.length) return <span className="muted">Inventário vazio</span>;
  return (
    <div className="inventory-tags">
      {entries.map(([tipo, qtd]) => (
        <span key={tipo}>{tipo}: <strong>{formatKg(qtd)}</strong></span>
      ))}
    </div>
  );
}

export default function Message({ type = 'info', children }) {
  if (!children) return null;
  return <div className={`message ${type}`}>{children}</div>;
}

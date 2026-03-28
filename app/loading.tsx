export default function Loading() {
  return (
    <div className="fixed top-0 left-0 right-0 z-[10000] pointer-events-none">
      <div className="h-1 lg:h-1.5 w-full bg-slate-100 overflow-hidden">
        <div className="h-full bg-gradient-to-r from-primary to-primary-container animate-progress-bar origin-left w-full shadow-[0_0_10px_rgba(0,177,79,0.5)]"></div>
      </div>
    </div>
  );
}

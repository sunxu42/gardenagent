interface GuideCurrentBadgeProps {
  label: string;
}

export function GuideCurrentBadge({ label }: GuideCurrentBadgeProps) {
  return (
    <span className="ml-2.5 inline-flex shrink-0 items-center rounded-full bg-emerald-500 px-2 py-0.5 text-[10px] font-medium leading-none text-white">
      {label}
    </span>
  );
}

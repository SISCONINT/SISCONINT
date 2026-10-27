import clsx from "clsx";
import { avatarTone, initials } from "../utils";

const SIZES = {
  sm: "size-8 text-[11px]",
  md: "size-10 text-xs",
  lg: "size-14 text-base",
  xl: "size-20 text-2xl",
} as const;

interface Props {
  name: string;
  size?: keyof typeof SIZES;
  className?: string;
}

export function ClientAvatar({ name, size = "md", className }: Props) {
  return (
    <span
      aria-hidden="true"
      className={clsx(
        "grid shrink-0 place-items-center rounded-xl font-display font-bold uppercase tracking-wide",
        SIZES[size],
        avatarTone(name),
        className,
      )}
    >
      {initials(name)}
    </span>
  );
}

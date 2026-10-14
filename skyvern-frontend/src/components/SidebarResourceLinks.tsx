import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { cn } from "@/util/utils";

type Props = {
  collapsed: boolean;
  billingLink?: { href: string; label: string; icon: ReactNode };
};

function SidebarResourceLinks({ collapsed, billingLink }: Props) {
  if (!billingLink) {
    return null;
  }

  return (
    <div
      className={cn(
        "border-t border-neutral-200 py-2 dark:border-white/[0.06]",
        {
          "px-2": collapsed,
          "px-3": !collapsed,
        },
      )}
    >
      <div
        className={cn("flex gap-1", {
          "flex-col items-center": collapsed,
          "flex-col": !collapsed,
        })}
      >
        <Link
          to={billingLink.href}
          title={collapsed ? billingLink.label : undefined}
          className={cn(
            "group flex h-7 items-center rounded-md border border-green-500/30 bg-green-500/10 text-[13px] font-medium leading-5 text-green-700 antialiased shadow-[inset_0_1px_0_rgba(255,255,255,0.65)] transition-colors duration-100 hover:bg-green-500/15 hover:text-green-800 dark:border-green-400/35 dark:bg-green-400/10 dark:text-green-300 dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] dark:hover:bg-green-400/20 dark:hover:text-green-200",
            {
              "w-7 justify-center": collapsed,
              "w-full gap-2.5 px-2": !collapsed,
            },
          )}
        >
          <span className="flex size-4 shrink-0 items-center justify-center text-green-700 transition-colors duration-100 group-hover:text-green-800 dark:text-green-300 dark:group-hover:text-green-200">
            {billingLink.icon}
          </span>
          {!collapsed ? (
            <span className="min-w-0 flex-1 truncate">{billingLink.label}</span>
          ) : null}
        </Link>
      </div>
    </div>
  );
}

export { SidebarResourceLinks };

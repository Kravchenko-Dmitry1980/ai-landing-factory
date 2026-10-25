import { AppHeader } from "@/components/shell/AppHeader";
import { requireUser } from "@/lib/session.server";

/** VR/AR showcase is a developer tool now; it keeps a plain container under the shared header. */
export default async function ShowcaseLayout({ children }: { children: React.ReactNode }) {
  const user = await requireUser("/showcase", "editor");
  return (
    <>
      <AppHeader user={user} current="studio" />
      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
    </>
  );
}

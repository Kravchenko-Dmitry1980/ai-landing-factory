import { AppHeader } from "@/components/shell/AppHeader";

/** VR/AR showcase is a developer tool now; it keeps a plain container under the shared header. */
export default function ShowcaseLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <AppHeader />
      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
    </>
  );
}

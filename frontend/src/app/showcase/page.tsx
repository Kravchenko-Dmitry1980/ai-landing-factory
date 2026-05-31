import { ShowcaseBuilder } from "@/components/showcase/ShowcaseBuilder";

export const metadata = {
  title: "VR/AR Showcase — AI Landing Factory",
};

export default function ShowcasePage() {
  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-3xl font-bold tracking-tight">VR/AR Showcase</h1>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          Соберите витрину из сгенерированных лендингов и демо-проектов
          (например, из AI Google Studio). Экспорт создаёт self-contained
          HTML с 3D-стендом A-Frame и доступным 2D-фолбэком.
        </p>
      </section>
      <ShowcaseBuilder />
    </div>
  );
}

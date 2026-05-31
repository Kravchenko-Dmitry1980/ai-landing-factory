import { ShowcaseList } from "@/components/showcase/ShowcaseList";

export const metadata = {
  title: "VR/AR витрина — AI Landing Factory",
};

export default function ShowcasePage() {
  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-3xl font-bold tracking-tight">VR/AR витрина</h1>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          Создавайте витрины из сгенерированных лендингов и демо-проектов
          (например, из AI Google Studio). Экспорт создаёт self-contained HTML
          с 3D-стендом A-Frame и доступным 2D-фолбэком, либо портативный ZIP
          для офлайн-демо.
        </p>
      </section>
      <ShowcaseList />
    </div>
  );
}

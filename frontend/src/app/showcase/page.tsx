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
          Demo-ready конструктор выставочного стенда: соберите витрину из
          сгенерированных лендингов, добавьте demo-ссылки AI Google Studio и
          экспортируйте portable ZIP для офлайн-показа руководству.
        </p>
      </section>
      <ShowcaseList />
    </div>
  );
}

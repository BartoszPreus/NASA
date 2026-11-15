import { useEffect } from "react";
import { useRoute } from "./lib/router";
import { Footer, Nav } from "./components/Shell";
import { useAtlas } from "./lib/data";
import { Landing } from "./pages/Landing";
import { Explore } from "./pages/Explore";
import { MoonPage } from "./pages/Moon";
import { MethodPage } from "./pages/Method";
import { SourcesPage } from "./pages/Sources";

export function App() {
  const route = useRoute();
  const atlas = useAtlas();
  useEffect(() => {
    if (route.page !== "explore") scrollTo({ top: 0, behavior: "instant" as ScrollBehavior });
  }, [route.page]);
  return (
    <>
      <Nav page={route.page} />
      <main id="main">
        {route.page === "home" && <Landing atlas={atlas} />}
        {route.page === "explore" && <Explore atlas={atlas} params={route.params} />}
        {route.page === "moon" && <MoonPage atlas={atlas} />}
        {route.page === "method" && <MethodPage />}
        {route.page === "sources" && <SourcesPage />}
      </main>
      {route.page !== "explore" && <Footer commit={atlas.data?.meta.commit} />}
    </>
  );
}

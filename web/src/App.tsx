import { lazy, Suspense, useEffect } from "react";
import { useRoute, type Route } from "./lib/router";
import { Footer, Nav } from "./components/Shell";
import { Loading } from "./components/kit";
import { useAtlas } from "./lib/data";
import { Landing } from "./pages/Landing";

// Pages other than the landing page load on demand, so three.js and the page code arrive when needed.
const Discover = lazy(() => import("./pages/Discover").then((m) => ({ default: m.Discover })));
const Explore = lazy(() => import("./pages/Explore").then((m) => ({ default: m.Explore })));
const ComparePage = lazy(() => import("./pages/Compare").then((m) => ({ default: m.ComparePage })));
const MoonPage = lazy(() => import("./pages/Moon").then((m) => ({ default: m.MoonPage })));
const MethodPage = lazy(() => import("./pages/Method").then((m) => ({ default: m.MethodPage })));
const SourcesPage = lazy(() => import("./pages/Sources").then((m) => ({ default: m.SourcesPage })));

const Irrigation = lazy(() => import("./irrigation/Planner"));

export function App() {
  const route = useRoute();
  if (route.page === "irrigation") return <>
    <Nav page="irrigation" />
    <main id="main" lang="pl"><Suspense fallback={<Loading text="Ładowanie planera" />}><Irrigation /></Suspense></main>
  </>;
  return <AtlasPage route={route} />;
}

function AtlasPage({ route }: { route: Route }) {
  const atlas = useAtlas();
  useEffect(() => {
    if (route.page !== "explore") scrollTo({ top: 0, behavior: "instant" as ScrollBehavior });
  }, [route.page]);
  const full = route.page === "explore" || route.page === "discover";
  return (
    <>
      <Nav page={route.page} />
      <main id="main">
        <Suspense fallback={<Loading text="Loading" />}>
          {route.page === "home" && <Landing atlas={atlas} />}
          {route.page === "discover" && <Discover atlas={atlas} params={route.params} />}
          {route.page === "explore" && <Explore atlas={atlas} params={route.params} />}
          {route.page === "compare" && <ComparePage atlas={atlas} params={route.params} />}
          {route.page === "moon" && <MoonPage atlas={atlas} />}
          {route.page === "method" && <MethodPage />}
          {route.page === "sources" && <SourcesPage />}
        </Suspense>
      </main>
      {!full && <Footer commit={atlas.data?.meta.commit} />}
    </>
  );
}

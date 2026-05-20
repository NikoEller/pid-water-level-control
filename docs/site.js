(function () {
  const username = window.location.hostname.split(".")[0];
  const segments = window.location.pathname.split("/").filter(Boolean);
  const repo = segments[0];

  if (!username || !repo) {
    return;
  }

  const repoBase = `https://github.com/${username}/${repo}`;

  document.querySelectorAll("[data-repo-path]").forEach((link) => {
    const path = link.getAttribute("data-repo-path");
    const kind = link.getAttribute("data-repo-kind") || "blob";
    link.href = `${repoBase}/${kind}/main/${path}`;
  });
})();

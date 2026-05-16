export function downloadCsv(filename, rows) {
    if (!rows || rows.length === 0) return;
    const headers = Object.keys(rows[0]);
    const lines = [
        headers.join(","),
        ...rows.map(row =>
            headers.map(h => {
                const val = row[h] ?? "";
                const str = String(val);
                return str.includes(",") || str.includes('"') || str.includes("\n")
                    ? `"${str.replaceAll('"', '""')}"`
                    : str;
            }).join(",")
        ),
    ];
    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

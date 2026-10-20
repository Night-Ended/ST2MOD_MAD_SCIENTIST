using System.Linq;
using Godot;
using HarmonyLib;
using MegaCrit.Sts2.Core.Models;

namespace MadScientist.MadScientistCode;

/// <summary>
/// Startup self-check (one line in the log): confirms the character model is
/// registered with the id BaseLib assigned to it, and that the packed art and
/// localization resolve through the .pck. Handy when something silently fails.
/// </summary>
[HarmonyPatch(typeof(ModelDb), nameof(ModelDb.Preload))]
internal static class MadScientistDiagnostics
{
    private static readonly string[] Resources =
    [
        "res://MadScientist/images/character/combat.png",
        "res://MadScientist/images/charui/char_select_mad_scientist.png",
        "res://MadScientist/images/charui/character_icon_mad_scientist.png",
        "res://MadScientist/images/charui/map_marker_mad_scientist.png",
    ];

    [HarmonyPostfix]
    private static void Postfix()
    {
        var character = ModelDb.All.OfType<CharacterModel>()
            .FirstOrDefault(c => c.GetType() == typeof(Character.MadScientist));

        if (character == null)
        {
            MainFile.Logger.Error("[Diag] MadScientist character model was not registered!");
            return;
        }

        var missing = Resources.Where(p => !ResourceLoader.Exists(p)).ToList();
        MainFile.Logger.Info(
            $"[Diag] OK {character.Id} title='{character.Title.GetFormattedText()}' " +
            $"hp={character.StartingHp} missingAssets={missing.Count}");

        foreach (var path in missing)
        {
            MainFile.Logger.Error($"[Diag] missing asset: {path}");
        }
    }
}

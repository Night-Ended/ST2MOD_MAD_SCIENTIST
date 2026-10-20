using BaseLib.Abstracts;
using BaseLib.Extensions;
using BaseLib.Utils;
using MadScientist.MadScientistCode.Character;
using MadScientist.MadScientistCode.Extensions;

namespace MadScientist.MadScientistCode.Potions;

[Pool(typeof(MadScientistPotionPool))]
public abstract class MadScientistPotion : CustomPotionModel
{
	public override string? CustomPackedImagePath =>
		$"{Id.Entry.RemovePrefix().ToLowerInvariant()}.png".PotionImagePath();
	public override string? CustomPackedOutlinePath =>
		$"{Id.Entry.RemovePrefix().ToLowerInvariant()}.png".PotionOutlineImagePath();
}
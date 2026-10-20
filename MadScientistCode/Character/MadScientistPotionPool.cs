using BaseLib.Abstracts;
using MadScientist.MadScientistCode.Extensions;
using Godot;

namespace MadScientist.MadScientistCode.Character;

public class MadScientistPotionPool : CustomPotionPoolModel
{
    public override Color LabOutlineColor => MadScientist.Color;
    

    public override string BigEnergyIconPath => "charui/big_energy.png".ImagePath();
    public override string TextEnergyIconPath => "charui/text_energy.png".ImagePath();
}